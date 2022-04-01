#! /usr/bin/env python3


from collections import defaultdict
from pathlib import Path

import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from ranking_utils import write_trec_eval_file


@hydra.main(config_path="config", config_name="prediction")
def main(config: DictConfig):
    dataset = instantiate(
        config.prediction_data, data_processor=instantiate(config.ranker.data_processor)
    )
    trainer = instantiate(config.trainer)

    result = defaultdict(dict)
    for item in trainer.predict(
        model=instantiate(config.ranker.model),
        dataloaders=instantiate(
            config.data_loader, dataset=dataset, collate_fn=dataset.collate_fn
        ),
        ckpt_path=config.ckpt_path,
    ):
        for index, score in zip(
            item["indices"].detach().numpy(), item["scores"].detach().numpy(),
        ):
            q_id, doc_id = dataset.get_ids(index)
            result[q_id][doc_id] = score

    # include the rank in the file name, otherwise multiple processes compete with each other
    out_file = Path.cwd() / f"predictions_{trainer.global_rank}.tsv"
    write_trec_eval_file(out_file, result, config.name)


if __name__ == "__main__":
    main()