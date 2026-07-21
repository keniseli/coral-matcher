import glob
import os
import numpy as np
from PIL import Image
import argparse
from collections.abc import Iterable
from multiprocessing import Pool
import sys

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
    """
    Track the progress of parallel task execution with a progress bar.

    The built-in :mod:`multiprocessing` module is used for process pools and
    tasks are done with :func:`Pool.map` or :func:`Pool.imap_unordered`.

    Args:
        func (callable): The function to be applied to each task.
        tasks (list or tuple[Iterable, int]): A list of tasks or
            (tasks, total num).
        nproc (int): Process (worker) number.
        initializer (None or callable): Refer to :class:`multiprocessing.Pool`
            for details.
        initargs (None or tuple): Refer to :class:`multiprocessing.Pool` for
            details.
        chunksize (int): Refer to :class:`multiprocessing.Pool` for details.
        bar_width (int): Width of progress bar.
        skip_first (bool): Whether to skip the first sample for each worker
            when estimating fps, since the initialization step may takes
            longer.
        keep_order (bool): If True, :func:`Pool.imap` is used, otherwise
            :func:`Pool.imap_unordered` is used.
    Returns:
        list: The task results.
    """
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


def parallel_main(data_dict):
    data=np.load(data_dict['raw_path'])
    mask_img=np.array(Image.open(data_dict['mask_path']).convert("L").resize((feature_size,feature_size),Image.NEAREST))
    for value in np.unique(mask_img):
        if value==0:
            continue
        for i in range(feat_dim):
            data[i,mask_img==value]=np.average(data[i,mask_img==value])  # shape should C * H * W , you can adjust this according to your feature shape
    np.save(data_dict['denoised_path'],data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Input specifications for generating augmented ground truth from sparse point labels.')

    # Paths - these are required
    parser.add_argument('-i', '--image_path', action='store', type=str, dest='image_path', help='the path to the images',
                        required=True)
    parser.add_argument("-m", '--mask_path', action='store',type=str, required=True, help="model type")
    parser.add_argument('-p', '--save_path', action='store', type=str, dest='save_path',
                        help='OPTIONAL: the destination of your propagated labels')

    parser.add_argument('--feat_dim', action='store', type=int, default=768, dest='feat_dim', help='feature dim')
    parser.add_argument('--feat_size', action='store', type=int, default=32, dest='feat_size', help='feature size')
    parser.add_argument('--back_cate', action='store', type=int, default=0, dest='back_cate', help='background category')

    # Save input arguments as variables
    args = parser.parse_args()
    feat_dim = args.feat_dim
    feature_size = args.feat_size
    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)

    filelist=[]
    for files in sorted(glob.glob(os.path.join(args.image_path, "*.npy"))):
        p,n=os.path.split(files)
        tmp_dict={}
        tmp_dict['raw_path']=files
        tmp_dict['mask_path']=os.path.join(args.mask_path,n.replace(".npy",".png"))
        if not os.path.exists(tmp_dict['mask_path']):
            continue
        tmp_dict['denoised_path']=os.path.join(args.save_path,n)
        filelist.append(tmp_dict)
    track_parallel_progress(parallel_main, filelist, 32)