# <img src="figs/coralsrt_logo.png" alt="The logo of CoralSRT" width="60" height="30"> CoralSRT: Revisiting Coral Reef Semantic Segmentation by Feature Rectification via Self-supervised Guidance

<a href="https://coralsrt.hkustvgd.com/"><img src="https://img.shields.io/badge/WEBSITE-Visit%20project%20page-blue?style=for-the-badge"></a>

<a href="https://coralsrt.hkustvgd.com/papers/CoralSRT.pdf"><img src="https://img.shields.io/badge/arXiv-Paper-<color>"></a>

Corals can grow in diverse shapes, textures, and regions, thus leading to high physical and appearance stochasticity.  It is challenging to acquire visually consistent knowledge for segmenting corals, in contrast to segmenting objects (e.g., fish).
We propose **CoralSRT**, an add-on self-supervised feature rectification module, to reduce the stochasticity of coral features. Our method requires no human annotations, retraining/fine-tuning FMs, or even domain-specific data. 
The key insight is to incorporate *self-repeated*, *asymmetric*, and *amorphous* properties of corals to strengthen within-segment affinity, leading to more efficient label propagation in feature space and producing significant semantic segmentation performance gains.


[Ziqiang Zheng](https://zhengziqiang.github.io/), Yuk-Kwan Wong, [Binh-Son Hua](https://sonhua.github.io/), [Jianbo Shi](https://www.cis.upenn.edu/~jshi/), [Sai-Kit Yeung](https://saikit.org/) 

> - Primary contact: Ziqiang Zheng (zhengziqiang1@gmail.com)

## 📢 News

[Sep.28 2024] We released the training codes and the pre-trained model of CoralSRT. 

[June 2025] CoralSRT was accepted by ICCV 2025.

## Overview

<p align="center">
    <img src="figs/coralsrt_teaser.jpg" width="100%"></a> <br>
    Teaser of CoralSRT.
</p>

Key Contributions:
* CoralSRT - **Revisiting coral segmentation from intrinsic properties of Corals**. 
* Demonstrated efficiency regarding data, model and optimization.
* Model-agnostic design to support `DINO`, `DINO v2`, `DINO v3`, `iBoT`, `SAM`, `SAM 2`, `CoralSCOP`.

Insights:
* **Self-affinity** - while different corals are highly dissimilar, individual corals within the same growth exhibit strong self-affinity.
* **Intrinsic properties incorporated** - we extract a pattern related to the intrinsic properties of each coral to strengthen within-segment affinity, aligning with centrality
* **Why not promptable segmentation** - we have comprehensively dissected why promptable segmentation, such as SAM, is less effectively for coral segmentation (especially sparse-to-dense).
* **Optimization friendly** - without requiring additional human supervision, retraining/finetuning FMs or even domain-specific data.

## Abstract
We investigate coral reef semantic segmentation, in which multifaceted factors, like genes, environmental changes, and internal interactions, can lead to highly unpredictable growth patterns. Existing segmentation approaches in both computer vision and coral reef communities have failed to incorporate the intrinsic properties of corals — specifically their self-repeated, asymmetric, and amorphous distribution of elements — into model design.
We propose **CoralSRT**, a feature rectification module via self-supervised guidance, to reduce the stochasticity of coral features extracted by pretrained foundation models (FMs), as demonstrated in our teaser. Our insight is that while different corals are highly dissimilar, individual corals within the same growth exhibit strong self-affinity.
Using a superset of features from FMs learned by various pretext tasks, we extract a pattern related to the intrinsic properties of each coral to strengthen within-segment affinity, aligning with centrality. We investigate features from FMs that were optimized by various pretext tasks on significantly large-scale unlabeled or labeled data, which already contain rich information for modeling both within-segment and cross-segment affinities, enabling the adaptation of FMs for coral segmentation.
**CoralSRT** can rectify features from FMs to more efficient features for label propagation and lead to further significant semantic segmentation performance gains — all without requiring additional human supervision, retraining/finetuning FMs, or even domain-specific data. These advantages help reduce human effort and the need for domain expertise in data collection and labeling.
Our method is easy to implement, and also task- and model-agnostic. **CoralSRT** bridges the self-supervised pre-training and supervised training in the feature space, also offering insights for segmenting elements/stuffs (*e.g.*, grass, plants, cells, and biofoulings).

## Framework

<p align="center">
    <img src="figs/coralsrt_method.jpg" width="100%">
    <br>
    Framework overview of the proposed <b>CoralSRT</b> to rectify features of frozen foundation models (FMs) based on model-generated mask guidance or human annotations. 
    We force features within each semantic-agnostic segment to approach its <b>centrality</b> to reduce the stochasticity of coral features, leading to more efficient features for label propagation in the feature space.
    On the right-hand side, we demonstrate <code>Rec(·)</code> learning high-dimensional features inside each segment via centrality (<i>e.g.</i>, median value), which remains stable between different inferior segments due to the intrinsic self-repeated and amorphous properties of corals.
</p>

## Motivation and reformulation

The coral reef semantic segmentation could be categorized as **stuff segmentation**. COCO-Stuff (Caesar *et al.*, 2018) conducted the first attempt to do stuff segmentation and summarized five key properties between “instances/things” and “stuffs”: *shape*, *size*, *parts*, *instances*, and *texture*. Inspired by this work, we have also summarized the challenges of conducting coral segmentation:

- **Amorphous distribution** leading to irregular boundaries. Corals often feature non-uniform, encrusting, or intricate growth patterns that defy simple geometric descriptions, such as irregular edges.
- **Repeatability or Fractality:** The structure of corals exhibits a self-similar, fractal-like nature, where patterns or arrangements recur at varying scales.
- **Diversity.** Corals or coral reefs consist of a wide variety of components, contributing to their complex appearance.
- **Self-occlusion:** Due to clustering or overlapping elements, parts of the structure obscure others, complicating visual interpretation.
- **Asymmetry.** The whole reef structure is usually asymmetric, with amorphous shapes.

**Failure of promptable segmentation**

<p align="center">
    <img src="figs/failure.jpg" width="100%">
    <br>
    Promptable segmentation models (<i>e.g.</i>, SAM and CoralSCOP) lead to 
    <i>under-inclusive</i> and <i>over-inclusive</i> outputs. 
    The mask with <span style="color: red;">red</span> edge is for illustration, not model-generated.
</p>

**Key differences between Instances and Stuff**

<p align="center">
    <img src="figs/structure.jpg" width="100%">
    <br>
    The key difference between segmenting the fish and the corals: the fish has a <code>visually consistent structural unit</code> while the corals do not have. No matter which part of the fish is occluded, we humans can almost imagine its boundary and shape. 
    But for corals, we cannot imagine a consistent output from two occluded inputs with different regions occluded. 
</p>

**Our formulation**

<p align="center">
    <img src="figs/formulation.jpg" width="100%">
    <br>
    Our simple and fundamental problem formulation for coral reef semantic segmentation: <i>segment</i> as the basis to model within-segment and cross-segment affinities. 
</p>

## Results

* PCA visualizaiton
<p align="center">
    <img src="figs/feature_comparison.jpg" width="100%">
    <br>
    PCA comparison (first 3 channels) of features from different algorithms and foundation models.   
</p>

* Sparse-to-dense conversion
<p align="center">
    <img src="figs/comparison.jpg" width="100%">
    <br>
    Sparse-to-dense conversion based on features from different algorithms and foundation models.   
</p>

* Zero-shot ability
<p align="center">
    <img src="figs/zero_shot_seaview.jpg" width="100%">
    <br>
    Zero-shot sparse-to-dense conversion results on the Seaview dataset.   
</p>

* Model-agnostic

<p align="center">
    <img src="figs/model_agnostic.jpg" width="100%">
    <br>
    Our model could promote the features from various foundation models.   
</p>

## Installation and Usage

Please refer to the `requirement.txt` for installation.

### Trained checkpoints
- [DINO](https://www.dropbox.com/scl/fo/abdxcl5th6gp75bu0p67e/AAQB4Ttz2-OvjIXk5yi71aE?rlkey=6op0x2h2ye052vupw8dbm0oiu&st=7d9d2uzb&dl=0). For DINO pre-trained models, we provide the checkpoint optimized on SeaView, CoralWorld-1M and CoralWorld.
The corresponding rectifier weights are also provided. `official_dinofeature_coralmask_batch32_ckpt_049999.pth` indicates the feature rectifier for the features from original DINO ViT-B.

### Example usage
For sparse-to-dense conversion and PCA visualization:

```
python dino_rectifier.py --image_path data/example_data/test_data/UCSD_Mosaics/images --point_path data/example_data/test_data/UCSD_Mosaics/50points --which_feat original --save_path results/original_50points --pretrained_weights checkpoints/coralworld_dino_checkpoint0100.pth --rectifier_weights checkpoints/coralworld_dinofeature_coralmask_batch32_ckpt_049999.pth
```

Please download the pre-trained weights and rectifier weights and put the weights at the `checkpoints`. If you want to use the original dino weights, please set `pretrained_weights` to None. Please specify the feature using `which_feat`: `original` feature or `rectified` feature.

Compute the mIoU:

```
python compute_miou.py --prediction_path results/original_50points --gt_path data/example_data/test_data/UCSD_Mosaics/GT
```

Please note that we did not mask out the background category when computing the per-class IoU since masking these areas will not penalize the wrongly misrecognized areas. 

### Training DINO rectifier

Data preparation: Please check `utils/parallel_prepare_mask.py` and `utils/parallel_average_feature.py` for more details. You should also save the features in the `npy` format from foundation models first.


Please refer to the data structure of [DVT](https://github.com/Jiawei-Yang/Denoising-ViT) for preparing the training data.

Training the dino rectifier: please refer to `train_example.sh` for more details.


## Updates:
- [x] Project page
- [x] Codes release
- [x] DINO rectification model release
- [ ] DINO v3, SAM and CoralSCOP rectification model release (estimated to be the middle of Nov 2025)
- [ ] Release of rectification model trained on a larger dataset 


##  Citing CoralSRT

If you find CoralSRT helpful, please consider citing:
```
@article{ziqiang2025coralsrt,
  title={CoralSRT: Revisiting Coral Reef Semantic Segmentation by Feature Rectification via Self-supervised Guidance},
  author={Zheng, Ziqiang and Wong, Yuk-Kwan and Hua, Binh-Son and Shi, Jianbo and Yeung, Sai-Kit},
  journal={IEEE/CVF International Conference on Computer Vision (ICCV)},
  year={2025}
}
```

We also encourage to cite these following valuable works:

```
@article{beijbom2015towards,
  title={Towards automated annotation of benthic survey images: Variability of human experts and operational modes of automation},
  author={Beijbom, Oscar and Edmunds, Peter J and Roelfsema, Chris and Smith, Jennifer and Kline, David I and Neal, Benjamin P and Dunlap, Matthew J and Moriarty, Vincent and Fan, Tung-Yung and Tan, Chih-Jui and others},
  journal={PloS one},
  year={2015},
  publisher={Public Library of Science San Francisco}
}
@inproceedings{alonso2018semantic,
  title={Semantic segmentation from sparse labeling using multi-level superpixels},
  author={Alonso, I{\~n}igo and Murillo, Ana C},
  booktitle={IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
  pages={5785--5792},
  year={2018},
  organization={IEEE}
}
@inproceedings{raine2024human,
  title={Human-in-the-Loop Segmentation of Multi-species Coral Imagery},
  author={Raine, Scarlett and Marchant, Ross and Kusy, Brano and Maire, Frederic and Sunderhauf, Niko and Fischer, Tobias},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)},
  pages={2723--2732},
  year={2024}
}
```

## Acknowledgement

+ [SAM](https://github.com/facebookresearch/segment-anything), [SAM 2](https://github.com/facebookresearch/sam2), [DINO](https://github.com/facebookresearch/dino), [DINO v2](https://github.com/facebookresearch/dinov2), [DINO v3](https://github.com/facebookresearch/dinov3) [CoralSCOP](https://github.com/zhengziqiang/CoralSCOP)
+ [DVT](https://github.com/Jiawei-Yang/Denoising-ViT), We use the same backbone for feature rectification as DVT.
+ [HIL](https://github.com/sgraine/HIL-coral-segmentation), HIL inspires us to do the sparse-to-dense conversion and we used HIL for comparison.


We sincerely thank the valuable discussions and suggestions from Prof. Manuel Aranda, Prof. David Suggett, Dr. Guoxin Cui and Dr. Eveline van der Steeg from KAUST. Without the insightful discussions with them, we cannot finish this project.
