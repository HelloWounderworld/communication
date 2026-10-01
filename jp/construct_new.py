import os
# --- 変更 1/2: 代入ではなく setdefault ---------------------------------------
# 以前は:
#     os.environ["TOKENIZERS_PARALLELISM"] = "false"
#     os.environ["CUDA_VISIBLE_DEVICES"]='0'
#
# `setdefault` なら、環境（supervisord、docker、シェル自体）がすでに定義した値を
# 尊重する。何も定義されていなければ以前と同じデフォルトになる
# — したがって CLI の挙動はまったく同じ。
#
# これがないと、サービスがこのファイルを import するだけで GPU 0 が強制され、
# supervisord の `environment=` が無視されてしまう。
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

from pipeline.denoiser import * 
from pipeline.denoiser.base import get_denoiser_class
from pipeline.treebuilder import *
from pipeline.capgenerator import * 
from pipeline.capgenerator import get_capgen_class
from pipeline.propgenerator import * 
from pipeline.propgenerator import get_propgen_class
from pipeline.constructpipe import * 
from pipeline.constructpipe import get_constructpipe_class

from utils.model_utils import load_pretrained_models
import utils.basic_utils as basic_utils


import warnings
warnings.filterwarnings("ignore")
from config import BuildArguments, HfArgumentParser
from dataclasses import asdict
import random 

from utils.basic_utils import seed_it


# --- 変更 2/2: 再利用可能な中核を切り出す -----------------------------------
def build(cfg, pretrained_models=None):
    """構築処理の中核。サービスから再利用できる。

    以前の `main()` との違い:

      1. 準備済みの `cfg` を受け取る — `sys.argv` は読まない。サービスには
         コマンドラインがない。呼び出し側が BuildArguments を組み立て、必要な
         ものを上書きする。

      2. 読み込み済みの `pretrained_models` を受け付ける。これが、リクエスト間で
         モデルを常駐させ続けることを可能にする点だ: 起動時に 1 回読み込み、
         呼び出しのたびにここへ渡す。

         None のとき（CLI の場合）は従来の方法で読み込む — だから
         `bash scripts/construct.sh` は以前と同じように動き続ける。

      3. `tree_meta` を返す。以前は `construct()` の結果は捨てられていた。
         今は API のレスポンスになる。

    `pretrained_models` 辞書には最低限、次が必要:
        cap_gen_model, cap_gen_processor        -> ステップ 1（キャプション生成）
        blip_itrtv_model, blip_itrtv_processor  -> ステップ 2,3,4,5,6
        sentence_transformer                    -> ステップ 6
    `glove_model` は None でもよい: 使うのは CapTree だけで、CapTree は retrieve 側のもの。
    """
    seed_it(cfg.seed)

    exp_dir = os.path.join(cfg.res_dir, cfg.construct_dir, cfg.collection, cfg.construct_name)
    cfg.exp_dir = exp_dir 
    os.makedirs(exp_dir, exist_ok=True)

    cfg_dict = asdict(cfg)
    basic_utils.save_json(cfg_dict, os.path.join(exp_dir, "settings.json"))

    if pretrained_models is None:
        pretrained_models = load_pretrained_models(cfg)

    caption_generator = get_capgen_class(cfg.caption_generator)(cfg, pretrained_models)
    caption_denoiser = get_denoiser_class(cfg.caption_denoiser)(cfg, pretrained_models)
    proposal_generator = get_propgen_class(cfg.proposal_generator)(cfg, pretrained_models)

    construct_pipeline = get_constructpipe_class(cfg.construct_pipeline)(cfg, caption_generator, caption_denoiser, proposal_generator, pretrained_models)

    return construct_pipeline.construct()


def main():
    print("Building parse pipeline")
    parser = HfArgumentParser(BuildArguments)
    cfg  = parser.parse_args_into_dataclasses(look_for_args_file=False)[0]
    print(cfg)

    build(cfg)

    print(cfg.construct_name)
    print("DONE!")

if __name__ == "__main__":
    main()
