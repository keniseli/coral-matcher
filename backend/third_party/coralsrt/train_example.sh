python train_dino_rectifier.py --model vit_base_patch16_dino --data_root ./ --feat_root data/denoised_feats/cocostuff/denoised_features/vit_base_patch16_dino --data_list_path data/{your_file_list}.txt --auto_stride --num_iterations 50000 --project "stage-2" --run_name "vit_base_patch16_dino" --batch_size 32 --num_workers 4

### {your_file_list}.txt should be like this:
### data/cocostuff/000000528030.jpg
### data/cocostuff/000000528033.jpg
### data/cocostuff/000000528046.jpg
### data/cocostuff/000000528047.jpg

