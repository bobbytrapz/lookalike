#!/usr/bin/env python
# based on facenet/src/compare.py from github.com/davidsandberg/facenet

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scipy import misc
import tensorflow as tf
import numpy as np
import sys
import os
import copy
import argparse
import facenet
import align.detect_face
import json
from pathlib import Path

SAVE_JSON_AS = 'lookalike.json'


def similarity(distance, min_distance=0):
    # given the distance between two faces
    # how similar are these two faces
    # compared to how similar any two different faces can be (min_distance)
    s = 1 / (1 + distance - min_distance)
    return round(s, 2)


def show_idol_info(idol):
    # print idol info to stdout
    print('name:', idol['name'], 'group:', idol['group'])

    print('  top')
    for group, i in idol['top'].items():
        print('  group:', group)
        print('  image_url:', i['image_url'])
        print('  similarity', i['similarity'])

    print('  top 10')
    for i in idol['top_10']:
        print('  name:', i['name'])
        print('  image_url:', i['image_url'])
        print('  similarity', i['similarity'])


def main(args):
    if len(args.names) > 0:
        with open(SAVE_JSON_AS, 'r') as f:
            data = json.load(f)
            for name in args.names:
                idol = data.get(name)
                if idol is not None:
                    show_idol_info(idol)
                    print(json.dumps(idol, indent=4))
        return

    # no names were given so let's compare all the faces
    filenames = list()
    for ext in ['jpg', 'png']:
        paths = Path("data/profile").glob("**/*.{}".format(ext))
        filenames.extend(str(p) for p in paths)

    images = load_and_align_data(
        filenames,
        args.image_size, args.margin, args.gpu_memory_fraction)
    with tf.Graph().as_default():

        with tf.Session() as sess:

            # Load the model
            facenet.load_model(args.model)

            # Get input and output tensors
            images_placeholder = tf.get_default_graph(
            ).get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph(
            ).get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph(
            ).get_tensor_by_name("phase_train:0")

            # Run forward pass to calculate embeddings
            print("Calculating embeddings for", len(images), 'images...')
            feed_dict = {images_placeholder: images,
                         phase_train_placeholder: False}
            emb = sess.run(embeddings, feed_dict=feed_dict)

            # for each image path extract the name and group
            faces = list()
            for p in (Path(fn) for fn in filenames):
                name = p.parent.name
                group = p.parent.parent.name.lower()
                faces.append({
                    "path": p,
                    "name": name,
                    "group": group,
                })

            # calculate the distances between each pair of faces
            min_dist = float('inf')
            idols = dict()
            for aii, a in enumerate(faces):
                # add a new idol
                idol = {
                    "name": a['name'],
                    "group": a['group'],
                    "image_url": str(a['path']),
                    "top": dict(),
                    "top_10": [],
                }
                print("[add idol]", idol['name'])

                # compare this idol to every other member
                for bii, b in enumerate(faces):
                    if aii == bii:
                        # do not compare with yourself
                        continue
                    dist = np.sqrt(np.sum(
                        np.square(np.subtract(emb[aii, :], emb[bii, :]))))
                    min_dist = min(dist, min_dist)

                    # add to top N
                    bd = {
                        "name": b['name'],
                        "group": b['group'],
                        "image_url": str(b['path']),
                        "dist": dist,
                    }
                    idol['top_10'].append(bd)
                    if len(idol['top_10']) > 10:
                        idol['top_10'].remove(
                            max(idol['top_10'], key=lambda k: k['dist']))

                    # add to top
                    group = bd['group']
                    g = idol['top'].get(group)
                    if g is None or bd['dist'] < g['dist']:
                        idol['top'][group] = bd
                    else:
                        idol['top'][group] = g

                # add this idol
                idols[idol['name']] = idol

            # calculate similarity for each idol
            for name, idol in idols.items():
                print("[calculate similarity]", name)
                idol['top_10'] = [{
                    "name": i['name'],
                    "group": i['group'],
                    "image_url": i['image_url'],
                    "similarity": similarity(i['dist'], min_dist),
                } for i in idol['top_10']]

                idol['top'] = {
                    k: {
                        "name": v['name'],
                        "group": v['group'],
                        "image_url": v['image_url'],
                        "similarity": similarity(v['dist'], min_dist),
                    }
                    for k, v in idol['top'].items()
                }

            # save to disk
            print("[save]", SAVE_JSON_AS)
            with open(SAVE_JSON_AS, 'w') as f:
                json.dump(idols, f)

            # the idols with the closest matches appear first
            # top = sorted(idols.values(),
            #              reverse=True,
            #              key=lambda i: max(t['similarity']
            #                                for t in i['top_10']))

            print("min_dist", min_dist)

            return


def load_and_align_data(image_paths, image_size, margin, gpu_memory_fraction):

    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor

    print('Creating networks and loading parameters')
    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(
            per_process_gpu_memory_fraction=gpu_memory_fraction)
        sess = tf.Session(config=tf.ConfigProto(
            gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)

    tmp_image_paths = copy.copy(image_paths)
    img_list = []
    for image in tmp_image_paths:
        print('[load]', image)
        img = misc.imread(os.path.expanduser(image), mode='RGB')
        img_size = np.asarray(img.shape)[0:2]
        bounding_boxes, _ = align.detect_face.detect_face(
            img, minsize, pnet, rnet, onet, threshold, factor)
        if len(bounding_boxes) < 1:
            image_paths.remove(image)
            print("can't detect face, remove ", image)
            continue
        det = np.squeeze(bounding_boxes[0, 0:4])
        bb = np.zeros(4, dtype=np.int32)
        bb[0] = np.maximum(det[0]-margin/2, 0)
        bb[1] = np.maximum(det[1]-margin/2, 0)
        bb[2] = np.minimum(det[2]+margin/2, img_size[1])
        bb[3] = np.minimum(det[3]+margin/2, img_size[0])
        cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
        aligned = misc.imresize(
            cropped, (image_size, image_size), interp='bilinear')
        prewhitened = facenet.prewhiten(aligned)
        img_list.append(prewhitened)
    images = np.stack(img_list)
    return images


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('names', type=str, nargs='*',
                        help='Names of idols')
    parser.add_argument('--model', type=str,
                        default="models/20180402-114759",
                        help="Could be either a directory containing the"
                        "meta_file and ckpt_file"
                        " or a model protobuf (.pb) file")
    parser.add_argument('--image_size', type=int,
                        default=160,
                        help="Image size (height, width) in pixels.")
    parser.add_argument('--margin', type=int,
                        default=44,
                        help="Margin for the crop around the bounding box"
                        " (height, width) in pixels.")
    parser.add_argument('--gpu_memory_fraction', type=float,
                        default=1.0,
                        help="Upper bound on the amount of GPU memory"
                        " that will be used by the process.")
    return parser.parse_args(argv)


if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
