# Copyright (c) Facebook, Inc. and its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import glob
import sys
import argparse
import requests
from io import BytesIO
import faiss
import torch.nn as nn
from torchvision import transforms as pth_transforms
from vis_utils import *
import seaborn as sns
import vision_transformer as vits
import dvt.models as DVT
import matplotlib
matplotlib.use("Agg")  # Safe for headless environments
import matplotlib.pyplot as plt

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sparse-to-dense conversion')
    parser.add_argument('--arch', default='vit_base', type=str,
                        choices=['vit_tiny', 'vit_small', 'vit_base'], help='Architecture (support only ViT atm).')
    parser.add_argument('--which_feat', default='rectified', type=str,
                        choices=['original', 'rectified'], help='Architecture (support only ViT atm).')
    parser.add_argument('--patch_size', default=16, type=int, help='Patch resolution of the model.')
    parser.add_argument('--pretrained_weights', default='', type=str,
                        help="Path to pretrained weights to load.")
    parser.add_argument('--rectifier_weights', default='', type=str,
                        help="Path to rectifier weights to load.")
    parser.add_argument("--checkpoint_key", default="teacher", type=str,
                        help='Key to use in the checkpoint (example: "teacher")')
    parser.add_argument("--image_size", default=(512, 512), type=int, nargs="+", help="Resize image.")
    parser.add_argument("--image_path", action='store', type=str, help="Path of the image to load.", required=True)
    parser.add_argument('--point_path', action='store', type=str, dest='point_path',
                        help='the path to the provided labels', required=True)
    parser.add_argument('--save_path', action='store', type=str, dest='save_path',
                        help='OPTIONAL: the destination of your propagated labels')
    parser.add_argument('--vis_path', action='store', type=str, dest='vis_path',
                        help='OPTIONAL: the destination of visualisations showing the propagated labels in RGB')
    args = parser.parse_args()

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    # build model
    model = vits.__dict__[args.arch](patch_size=args.patch_size, num_classes=0)
    for p in model.parameters():
        p.requires_grad = False
    model.eval()
    model.to(device)
    if os.path.isfile(args.pretrained_weights):
        state_dict = torch.load(args.pretrained_weights, map_location="cpu")
        if args.checkpoint_key is not None and args.checkpoint_key in state_dict:
            print(f"Take key {args.checkpoint_key} in provided checkpoint dict")
            state_dict = state_dict[args.checkpoint_key]
        # remove `module.` prefix
        state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
        # remove `backbone.` prefix induced by multicrop wrapper
        state_dict = {k.replace("backbone.", ""): v for k, v in state_dict.items()}
        msg = model.load_state_dict(state_dict, strict=False)
        print('Pretrained weights found at {} and loaded with msg: {}'.format(args.pretrained_weights, msg))
    else:
        print("Please use the `--pretrained_weights` argument to indicate the path of the checkpoint to evaluate.")
        url = None
        if args.arch == "vit_small" and args.patch_size == 16:
            url = "dino_deitsmall16_pretrain/dino_deitsmall16_pretrain.pth"
        elif args.arch == "vit_small" and args.patch_size == 8:
            url = "dino_deitsmall8_300ep_pretrain/dino_deitsmall8_300ep_pretrain.pth"  # model used for visualizations in our paper
        elif args.arch == "vit_base" and args.patch_size == 16:
            url = "dino_vitbase16_pretrain/dino_vitbase16_pretrain.pth"
        elif args.arch == "vit_base" and args.patch_size == 8:
            url = "dino_vitbase8_pretrain/dino_vitbase8_pretrain.pth"
        if url is not None:
            print("Since no pretrained weights have been provided, we load the reference pretrained DINO weights.")
            state_dict = torch.hub.load_state_dict_from_url(url="https://dl.fbaipublicfiles.com/dino/" + url)
            model.load_state_dict(state_dict, strict=True)
        else:
            print("There is no reference weights available for this model => We use random weights.")

    # open image
    if args.image_path is None:
        # user has not specified any image - we use our own image
        print("Please use the `--image_path` argument to indicate the path of the image you wish to visualize.")
        print("Since no image path have been provided, we take the first image in our paper.")
        response = requests.get("https://dl.fbaipublicfiles.com/dino/img.png")
        img = Image.open(BytesIO(response.content))
        img = img.convert('RGB')
    elif os.path.isdir(args.image_path):
        test_imgs = []
        names = []
        for files in sorted(glob.glob(os.path.join(args.image_path, "*.*")))[:10]:
            p, n = os.path.split(files)
            names.append(n)
            with open(files, 'rb') as f:
                img = Image.open(f)
                img = img.convert('RGB')
                test_imgs.append(img)
    else:
        print(f"Provided image path {args.image_path} is non valid.")
        sys.exit(1)
    transform = pth_transforms.Compose([
        pth_transforms.Resize(args.image_size),
        pth_transforms.ToTensor(),
        pth_transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])


    image_path = args.image_path
    point_path = args.point_path
    save_path = args.save_path
    vis_path= args.vis_path
    os.makedirs(os.path.join(save_path,"pca"),exist_ok=True)
    if vis_path is not None:
        os.makedirs(vis_path,exist_ok=True)

    k=1
    if args.arch=='vit_base':
        num_feats=768
    else:
        num_feats=384
    image_width, image_height = args.image_size[0],args.image_size[1]

    pos_w = args.image_size[0]//args.patch_size
    pos_h = args.image_size[1]//args.patch_size

    rectifier = DVT.Denoiser(
        noise_map_height=pos_h,
        noise_map_width=pos_w,
        feat_dim=num_feats,
        vit=None,
        num_blocks=1,
    )

    original = torch.load(args.rectifier_weights,
                          map_location=torch.device('cpu'))  #
    new_state_dict = {}
    for key, value in original['denoiser'].items():
        new_state_dict[key] = value
    rectifier.load_state_dict(new_state_dict, strict=True)
    rectifier=rectifier.to(device)

    for cnt, img_pil in enumerate(test_imgs):
        img = transform(img_pil)
        name = names[cnt]
        # make the image divisible by the patch size
        w, h = img.shape[1] - img.shape[1] % args.patch_size, img.shape[2] - img.shape[2] % args.patch_size
        img = img[:, :w, :h].unsqueeze(0)

        w_featmap = img.shape[-2] // args.patch_size
        h_featmap = img.shape[-1] // args.patch_size

        with torch.no_grad():
            layers = model.get_intermediate_layers(img.to(device), 1)
            # attentions = model.get_last_selfattention(img.to(device))
            raw_features = layers[0][0, 1:, :].reshape(w_featmap, h_featmap, -1).unsqueeze(0).float()
            rectified_features = rectifier(raw_features)
            rectified_features = torch.permute(rectified_features, (0, 3, 1, 2))

        raw_features = nn.functional.interpolate(torch.permute(raw_features, (0, 3, 1, 2)),
                                                 scale_factor=args.patch_size, mode='bilinear')
        rectified_features = nn.functional.interpolate(rectified_features, scale_factor=args.patch_size, mode='bilinear')

        if args.which_feat == "original":
            features = raw_features[0]
        else:
            features = rectified_features[0]

        raw_features_pca=pca_sklearn_gpu(torch.permute(raw_features, (0, 2, 3, 1))[0], feature_size=(pos_h*args.patch_size,pos_w*args.patch_size),
                        num_feats=num_feats,
                        num_components=3)

        rectified_features_pca = pca_sklearn_gpu(torch.permute(rectified_features, (0, 2, 3, 1))[0],
                                           feature_size=(pos_h * args.patch_size, pos_w * args.patch_size),
                                           num_feats=num_feats,
                                           num_components=3)

        vis_fig, vis_axes = plt.subplots(1, 3, figsize=(12, 4))
        vis_axes[0].imshow(img_pil)
        vis_axes[1].imshow(normalize_to_range(raw_features_pca.detach().cpu()))
        vis_axes[2].imshow(normalize_to_range(rectified_features_pca.detach().cpu()))

        # plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(save_path, "pca", name),
                    bbox_inches="tight",
                    pad_inches=0)
        # Clear the current figure (axes, content)
        plt.clf()
        # Close the current figure window
        plt.close()
        # Close all open figure windows
        plt.close('all')
        # If using pyplot state machine, can also clear the current axes
        plt.cla()

        GT_pil_img = Image.open(os.path.join(point_path, name.replace(".jpg", ".png"))).resize(
            (image_width, image_height), Image.NEAREST)
        GT_mask_np = np.array(GT_pil_img)
        GT_mask_torch = torch.from_numpy(GT_mask_np)  # shape = [image_size,image_size]

        sparse_labels = torch.unsqueeze(torch.unsqueeze(GT_mask_torch, 0), 0).to(device)

        if vis_path is not None:
            save_labels(name, image_path, vis_path, sparse_labels)

        sparse_labels_ft = torch.permute(torch.flatten(sparse_labels[0], 1, 2),
                                         (1, 0))  # shape = [image_size x image_size, 1]
        features_ft = torch.permute(torch.flatten(features, 1, 2), (1, 0))  # shape = [image_size x image_size, 1024]

        # template = torch.where(sparse_labels_ft > 0, features_ft, 0)
        template = torch.where(sparse_labels_ft > 0, features_ft,
                               torch.from_numpy(np.zeros([image_width * image_height, num_feats], dtype=np.float32)).to(
                                   device))

        labeled_features = template[abs(template).sum(dim=1) != 0]  # shape = [num_labelled_points, 1024]

        # Obtain the class of our labeled features
        labeled_points = torch.squeeze(sparse_labels_ft[abs(sparse_labels_ft).sum(dim=1) != 0],
                                       1)  # shape = [num_labelled_points]
        _, counts = torch.unique(labeled_points, return_counts=True)

        # print("Stage1 finished")
        del template, sparse_labels_ft
        torch.cuda.empty_cache()

        x = np.ascontiguousarray(labeled_features.cpu().numpy()).astype(
            np.float32)  # labeled_features shape = [num_labelled_points, 1024]
        q = np.ascontiguousarray(features_ft.cpu().numpy()).astype(
            np.float32)  # shape = [image_size x image_size, 1024]

        res = faiss.StandardGpuResources()  # use a single GPU

        upsample = torch.nn.Upsample((image_width, image_height),
                                     mode='nearest')  # shape = [1, 1, image_size, image_size]

        # print("Stage2 finished")
        # if we do L2 normalization and then use the metric inner product, the result is the cosine similarity
        # https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances
        index = faiss.index_factory(num_feats, "Flat", faiss.METRIC_INNER_PRODUCT)
        gpu_index = faiss.index_cpu_to_gpu(res, 0, index)
        gpu_index.ntotal
        faiss.normalize_L2(x)
        gpu_index.add(x)
        faiss.normalize_L2(q)
        similarities, sorted_indices = gpu_index.search(q, k)
        gpu_index.reset()

        labeled_points = labeled_points.cpu().numpy()
        sorted_classes = labeled_points[sorted_indices] - 1  # shape = [image_size x image_size, k]
        similarities_torch = torch.from_numpy(similarities)

        # print("Stage3 finished")
        if k > 1:
            sorted_classes = torch.from_numpy(sorted_classes)
            new_nearest = torch.mode(sorted_classes)[0]
            new_similarity_mask_torch = torch.reshape(new_nearest, (image_width, image_height))

        else:
            new_similarity_mask_torch = torch.reshape(torch.from_numpy(sorted_classes[:, 0]), (image_width, image_height))

        similarity_mask_upsample = upsample(
            new_similarity_mask_torch.unsqueeze(0).unsqueeze(0).float()).squeeze().int().to(
            device)  # shape = [1, 1, orig_image_size, orig_image_size]

        similarity_mask_upsample_np = similarity_mask_upsample.clone().cpu().numpy()

        # print("Stage4 finished")
        if save_path is not None:
            # Save the propagated mask as a .png file in the specified directory
            propagated_as_image = Image.fromarray(similarity_mask_upsample_np.astype(np.uint8))
            propagated_as_image.save(os.path.join(save_path, name[:-4]) + ".png", "PNG")

        if vis_path is not None:
            save_output_mask(np.uint8(new_similarity_mask_torch.cpu().numpy()), sparse_labels.int(), name[:-4],
                             vis_path,image_size=512)
