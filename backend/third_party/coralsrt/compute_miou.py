import os
import glob
import numpy as np
from PIL import Image
import argparse

def compute_miou_and_pixel_accuracy(predictions, ground_truth, ignored_cate=34):
    # Flatten the arrays
    predictions = predictions.flatten()
    ground_truth = ground_truth.flatten()
    predicted_values=list(np.unique(ground_truth))
    if ignored_cate in predicted_values:
        predicted_values.remove(ignored_cate)

    intersection = np.zeros(len(predicted_values))
    union = np.zeros(len(predicted_values))

    pixel_accuracies = np.zeros(len(predicted_values))

    for cls,predicted_value in enumerate(predicted_values):

        intersection[cls] = np.sum((predictions == predicted_value) & (ground_truth == predicted_value))
        union[cls] = np.sum((predictions == predicted_value) | (ground_truth == predicted_value))

        if np.sum(predictions==predicted_value) == 0:
            pixel_accuracies[cls]=.0
        else:
            pixel_accuracies[cls]= np.sum((predictions == ground_truth) & (predictions==predicted_value)) / np.sum(predictions==predicted_value)
    # Calculate mIoU
    iou = intersection / (union + 1e-6)  # Adding a small value to avoid division by zero
    mIoU = np.mean(iou)
    mpa = np.mean(pixel_accuracies)
    return mIoU, mpa

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Compute mIoU')
    parser.add_argument('--image_size', default=512, type=int, help='Patch resolution for computation.')
    parser.add_argument('--ignored_cate', default=34, type=int, help='The category should be ignored, for example, 34 for UCSD Mosaics dataset')
    parser.add_argument("--prediction_path", action='store', type=str, help="Path of the image to load.", required=True)
    parser.add_argument('--gt_path', action='store', type=str, dest='gt_path',
                        help='the path to the provided labels', required=True)

    args = parser.parse_args()
    img_size=args.image_size
    prediction_path=args.prediction_path
    gt_path=args.gt_path
    ignored_cate = args.ignored_cate

    mious,pixaccs=[],[]
    for files in glob.glob(os.path.join(prediction_path,"*.png")):
        p,n=os.path.split(files)
        predicted = np.array(Image.open(files).convert("L").resize((img_size, img_size), Image.NEAREST))
        gt=np.array(Image.open(os.path.join(gt_path,n)).convert("L").resize((img_size,img_size),Image.NEAREST))
        miou,pas=compute_miou_and_pixel_accuracy(predicted,gt,ignored_cate)
        mious.append(miou)
        pixaccs.append(pas)
    print(np.average(mious))
    print(np.average(pixaccs))