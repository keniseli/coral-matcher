import os
import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms


# Re-direct the framework to point inside our local packaged directory path
local_weights_dir = os.path.join(os.getcwd(), "weights")
os.environ["TORCH_HOME"] = local_weights_dir

device = torch.device("cpu")

resnet_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
resnet_model = torch.nn.Sequential(*list(resnet_model.children())[:-1])
resnet_model.eval()

transform_pipeline = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def generate_vector_embedding(cv2_image):
    """ Transforms an OpenCV image matrix into a 512-dimension spatial vector array. """
    rgb_img = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    tensor_img = transform_pipeline(rgb_img).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding_tensor = torch.squeeze(resnet_model(tensor_img))
        return embedding_tensor.cpu().numpy().tolist()
