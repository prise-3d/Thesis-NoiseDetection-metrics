# main imports
import sys, os, argparse
import numpy as np
import math

# image processing imports
from PIL import Image
import matplotlib.pyplot as plt

import ipfml.iqa.fr as fr_iqa
from ipfml import utils

# modules and config imports
sys.path.insert(0, '') # trick to enable import of main folder module

import custom_config as cfg
from modules.utils import data as dt
from data_attributes import get_image_features

# getting configuration information
zone_folder         = cfg.zone_folder
min_max_filename    = cfg.min_max_filename_extension

# define all scenes values
scenes_list         = cfg.scenes_names
scenes_indices      = cfg.scenes_indices
choices             = cfg.normalization_choices
zones               = cfg.zones_indices
seuil_expe_filename = cfg.seuil_expe_filename

features_choices    = cfg.features_choices_labels

max_nb_bits         = 8
display_error       = False


def display_svd_values(p_scene, p_thresholds, p_interval, p_indices, p_feature, p_mode, p_step, p_norm, p_ylim, p_label):
    """
    @brief Method which gives information about svd curves from zone of picture
    @param p_scene, scene expected to show svd values
    @param p_interval, interval [begin, end] of svd data to display
    @param p_interval, interval [begin, end] of samples or minutes from render generation engine
    @param p_feature, feature computed to show
    @param p_mode, normalization's mode
    @param p_norm, normalization or not of selected svd data
    @param p_ylim, ylim choice to better display of data
    @return nothing
    """

    max_value_svd = 0
    min_value_svd = sys.maxsize

    begin_data, end_data = p_interval
    begin_index, end_index = p_indices

    # go ahead selected scene
    scene_path = p_scene

    # construct each zones folder name
    zones_folder = []

    # get zones list info
    for index in zones:
        index_str = str(index)
        if len(index_str) < 2:
            index_str = "0" + index_str

        current_zone = "zone"+index_str
        zones_folder.append(current_zone)

    images_data = []
    images_indices = []

    threshold_learned_zones = []

    # get all images of folder
    scene_images = sorted([os.path.join(scene_path, img) for img in os.listdir(scene_path) if cfg.scene_image_extension in img])
    number_scene_image = len(scene_images)
    
    _, scene_name = os.path.split(p_scene)
    threshold_learned_zones = p_thresholds[scene_name]

    threshold_mean = np.mean(np.asarray(threshold_learned_zones))
    threshold_image_found = False

    svd_data = []


    # for each images
    for id_img, img_path in enumerate(scene_images):
        
        current_quality_image = dt.get_scene_image_quality(img_path)

        img = Image.open(img_path)

        svd_values = get_image_features(p_feature, img)

        if p_norm:
            svd_values = svd_values[begin_data:end_data]

        #svd_values = np.asarray([math.log(x) for x in svd_values])

        # update min max values
        min_value = svd_values.min()
        max_value = svd_values.max()

        if min_value < min_value_svd:
            min_value_svd = min_value

        if max_value > min_value_svd:
            max_value_svd = max_value

        # keep in memory used data
        if current_quality_image % p_step == 0:
            if current_quality_image >= begin_index and current_quality_image <= end_index:

                images_indices.append(dt.get_scene_image_postfix(img_path))
                svd_data.append(svd_values)

        if threshold_mean < current_quality_image and not threshold_image_found:

            threshold_image_found = True
            threshold_image_zone = current_quality_image

            print("Quality mean : ", current_quality_image, "\n")
            
            if dt.get_scene_image_postfix(img_path) not in images_indices:
                images_indices.append(dt.get_scene_image_postfix(img_path))

        print('%.2f%%' % ((id_img + 1) / number_scene_image * 100))
        sys.stdout.write("\033[F")


    # all indices of picture to plot
    print(images_indices)

    for id, data in enumerate(svd_data):

        # current_data = [ math.log10(d + 1.) for d in data ]
        # print(current_data)

        current_data = data

        if not p_norm:
            current_data = current_data[begin_data:end_data]

        if p_mode == 'svdn':
            current_data = utils.normalize_arr(current_data)

        if p_mode == 'svdne':
            current_data = utils.normalize_arr_with_range(current_data, min_value_svd, max_value_svd)

        images_data.append(current_data)


    # display all data using matplotlib (configure plt)
    fig, ax = plt.subplots(figsize=(30, 15))
    ax.set_facecolor('#FFFFFF')
    #fig.patch.set_facecolor('#F9F9F9')

    ax.tick_params(labelsize=26)
    #plt.rc('xtick', labelsize=22)
    #plt.rc('ytick', labelsize=22)

    #plt.title(p_scene + ' scene interval information SVD['+ str(begin_data) +', '+ str(end_data) +'], from scenes indices [' + str(begin_index) + ', '+ str(end_index) + '], ' + p_feature + ' feature, ' + p_mode + ', with step of ' + str(p_step) + ', svd norm ' + str(p_norm), fontsize=24)
    ax.set_ylabel('Component values', fontsize=36)
    ax.set_xlabel('Singular value component indices', fontsize=36)

    for id, data in enumerate(images_data):

        #p_label = p_scene + "_" + images_indices[id]
        p_label = images_indices[id] + " samples"

        if int(images_indices[id]) == int(threshold_image_zone):
            ax.plot(data, label=p_label + " (threshold mean)", lw=8, color='red')
        else:
            ax.plot(data, label=p_label, lw=4)

    plt.legend(bbox_to_anchor=(0.60, 0.98), loc=2, borderaxespad=0.2, fontsize=32)

    start_ylim, end_ylim = p_ylim
    ax.set_ylim(start_ylim, end_ylim)

    plot_name = scene_name + '_' + p_feature + '_' + str(p_step) + '_' + p_mode + '_' + str(p_norm) + '.png'
    # plt.title('Tend of Singular values at different samples of ' + p_label + ' scene', fontsize=40)
    plt.savefig(plot_name, transparent=True)

def main():

    parser = argparse.ArgumentParser(description="Display SVD data of scene")

    parser.add_argument('--scene', type=str, help='scene folder to use', required=True)
    parser.add_argument('--thresholds', type=str, help='expected thresholds file', required=True)
    parser.add_argument('--interval', type=str, help='Interval value to keep from svd', default='"0, 200"')
    parser.add_argument('--indices', type=str, help='Samples interval to display', default='"0, 900"')
    parser.add_argument('--feature', type=str, help='feature data choice', choices=features_choices)
    parser.add_argument('--mode', type=str, help='Kind of normalization level wished', choices=cfg.normalization_choices)
    parser.add_argument('--step', type=int, help='Each step samples to display', default=10)
    parser.add_argument('--norm', type=int, help='If values will be normalized or not', choices=[0, 1])
    parser.add_argument('--ylim', type=str, help='ylim interval to use', default='0,1')
    parser.add_argument('--label', type=str, help='output label name', default="")

    args = parser.parse_args()

    p_scene    = args.scene
    p_thresholds = args.thresholds
    p_indices  = list(map(int, args.indices.split(',')))
    p_interval = list(map(int, args.interval.split(',')))
    p_feature  = args.feature
    p_mode     = args.mode
    p_step     = args.step
    p_norm     = args.norm
    p_ylim     = list(map(float, args.ylim.split(',')))
    p_label    = args.label

    # 1. retrieve human_thresholds
    human_thresholds = {}

    # extract thresholds
    with open(p_thresholds) as f:
        thresholds_line = f.readlines()

        for line in thresholds_line:
            data = line.split(';')
            del data[-1] # remove unused last element `\n`
            current_scene = data[0]
            thresholds_scene = data[1:]

            # TODO : check if really necessary
            if current_scene != '50_shades_of_grey':
                human_thresholds[current_scene] = [ int(threshold) for threshold in  thresholds_scene ]

    display_svd_values(p_scene, human_thresholds, p_interval, p_indices, p_feature, p_mode, p_step, p_norm, p_ylim, p_label)

if __name__== "__main__":
    main()
