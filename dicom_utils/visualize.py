import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as _np


# %%
def quickplot(image, s=None, title=''):
    image_np = sitk.GetArrayFromImage(image)
    if s is None:
        s = image_np.shape[0] // 2
    plt.figure()
    plt.imshow(image_np[s, :, :], 'gray')
    plt.title(title)
    plt.show()


def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)


def multi_slice_viewer(volume, mask=None):
    volume = sitk.GetArrayViewFromImage(volume)
    volume = _np.transpose(volume, (1, 2, 0))
    if mask is not None:
        mask = sitk.GetArrayViewFromImage(mask)
        mask = _np.transpose(mask, (1, 2, 0))
    remove_keymap_conflicts({'j', 'k'})
    fig, ax = plt.subplots()

    ax.volume = volume
    ax.mask = mask

    ax.index = volume.shape[2] // 2

    ax.imshow(volume[:, :, ax.index], 'gray')
    if ax.mask is not None:
        ax.imshow(ax.mask[:, :, ax.index], alpha=0.25, vmax=_np.max(mask), vmin=_np.min(mask))

    fig.canvas.mpl_connect('key_press_event', process_key)


def process_key(event):
    fig = event.canvas.figure
    ax = fig.axes[0]
    if event.key == 'j':
        previous_slice(ax)
    elif event.key == 'k':
        next_slice(ax)
    fig.canvas.draw()


def previous_slice(ax):
    volume = ax.volume
    ax.index = (ax.index - 1) % volume.shape[2]  # wrap around using %
    ax.images[0].set_array(volume[:, :, ax.index])
    if ax.mask is not None:
        ax.images[1].set_array(ax.mask[:, :, ax.index])


def next_slice(ax):
    volume = ax.volume
    ax.index = (ax.index + 1) % volume.shape[2]
    ax.images[0].set_array(volume[:, :, ax.index])
    if ax.mask is not None:
        ax.images[1].set_array(ax.mask[:, :, ax.index])
