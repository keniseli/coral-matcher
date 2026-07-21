import glob
import os
import numpy as np
from PIL import Image
import json
import pycocotools.mask as mask
from collections.abc import Iterable
from multiprocessing import Pool
import sys
import argparse
def init_pool(process_num, initializer=None, initargs=None):
    if initializer is None:
        return Pool(process_num)
    elif initargs is None:
        return Pool(process_num, initializer)
    else:
        if not isinstance(initargs, tuple):
            raise TypeError('"initargs" must be a tuple')
        return Pool(process_num, initializer, initargs)
def track_parallel_progress(func,
                            tasks,
                            nproc,
                            initializer=None,
                            initargs=None,
                            bar_width=50,
                            chunksize=1,
                            skip_first=False,
                            keep_order=True,
                            file=sys.stdout):
    if isinstance(tasks, tuple):
        assert len(tasks) == 2
        assert isinstance(tasks[0], Iterable)
        assert isinstance(tasks[1], int)
        task_num = tasks[1]
        tasks = tasks[0]
    elif isinstance(tasks, Iterable):
        task_num = len(tasks)
    else:
        raise TypeError(
            '"tasks" must be an iterable object or a (iterator, int) tuple')
    pool = init_pool(nproc, initializer, initargs)
    start = not skip_first
    task_num -= nproc * chunksize * int(skip_first)
    results = []
    if keep_order:
        gen = pool.imap(func, tasks, chunksize)
    else:
        gen = pool.imap_unordered(func, tasks, chunksize)
    for result in gen:
        results.append(result)
        if skip_first:
            if len(results) < nproc * chunksize:
                continue
            elif len(results) == nproc * chunksize:
                continue
    pool.close()
    pool.join()
    return results

def prepare_mask(data_dict):
    output_annos=[]
    with open(data_dict['pos_json'], "r", encoding='utf-8') as f_labeled:
        aa_labeled = json.loads(f_labeled.read())
        images = aa_labeled['image']
        width,height=images['width'],images['height']
        max_area= width * height * 0.5
        annotations = aa_labeled['annotations']
        for item in annotations:
            if item['area'] > 4096 and item['area']<max_area:
                output_annos.append(item)
    item_mask = np.zeros([images['height'], images['width']])
    for i,tmp in enumerate(output_annos):
        mask_arr = mask.decode(tmp['segmentation'])
        item_mask[mask_arr == 1] = i + 1
    mask_img = Image.fromarray(np.uint8(item_mask), "L")
    mask_img.save(data_dict['mask_file'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Input specifications for generating augmented ground truth from sparse point labels.')
    parser.add_argument('--json_path', action='store', type=str, dest='json_path', help='the path to the jsons',
                        required=True)
    parser.add_argument('--mask_path', action='store',type=str, required=True, help="mask path")
    args = parser.parse_args()
    filelist=[]
    for files in glob.glob(os.path.join(args.json_path,"*.json")):
        data_dict={}
        data_dict['pos_json']=files
        p,n=os.path.split(files)
        data_dict['mask_file'] = os.path.join(args.mask_path,n.replace(".json",".png")) 
        filelist.append(data_dict)
    track_parallel_progress(prepare_mask, filelist, 32)

