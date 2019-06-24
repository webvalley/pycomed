import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np

import dicom_utils as du


def command_iteration(method):
    print("{0:3} = {1:10.5f} : {2}".format(method.GetOptimizerIteration(),
                                           method.GetMetricValue(),
                                           method.GetOptimizerPosition()))


def main():
    PATH_1 = f'/Volumes/Samsung T5/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/11'
    PATH_2 = f'/Volumes/Samsung T5/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/8'
    moving_image = du.load_series(PATH_1)
    moving_image = sitk.Cast(moving_image, sitk.sitkFloat32)
    fixed_image = du.load_series(PATH_2)
    fixed_image = sitk.Cast(fixed_image, sitk.sitkFloat32)
    moving_image_np = sitk.GetArrayFromImage(moving_image)
    print(np.shape(moving_image_np))
    plt.imshow(moving_image_np[int(np.size(moving_image_np, 0) / 2), :, :])
    plt.show()
    fixed_image_np = sitk.GetArrayFromImage(fixed_image)
    print(np.shape(fixed_image_np))
    plt.imshow(fixed_image_np[int(np.size(fixed_image_np, 0) / 2), :, :])
    plt.show()
    r_image = du.perform_registration(moving_image, fixed_image)
    r_image_np = sitk.GetArrayFromImage(r_image)
    print(np.shape(fixed_image_np))
    plt.imshow(r_image_np[int(np.size(r_image_np, 0) / 2), :, :])
    plt.show()


if __name__ == '__main__':
    main()
