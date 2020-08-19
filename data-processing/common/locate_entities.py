import logging
import os.path
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import cv2
import numpy as np

from common.bounding_box import extract_bounding_boxes
from common.compile import get_output_files
from common import directories
from common.types import BoundingBox
from common.types import RelativePath, ArxivId


@dataclass(frozen=True)
class LocationResult:
    locations: Dict[str, List[BoundingBox]]
    shifted_entities: List[str]
    first_shifted_entity: Optional[str]
    black_pixels_found: bool


def locate_entities(
    diff_images_dir: RelativePath, arxiv_id: ArxivId, entity_hues: Dict[str, float]
) -> Optional[LocationResult]:

    # Get output file names from results of compiling the uncolorized TeX sources.
    output_files = get_output_files(
        directories.arxiv_subdir("compiled-sources", arxiv_id)
    )
    output_paths = [f.path for f in output_files]

    black_pixels_found = False
    entity_locations: Dict[str, List[BoundingBox]] = defaultdict(list)

    for relative_file_path in output_paths:
        diff_images_file_path = os.path.join(diff_images_dir, relative_file_path)
        page_images = {}
        if not os.path.exists(diff_images_file_path):
            logging.warning(  # pylint: disable=logging-not-lazy
                "Expected but could not find a directory %s from the image diffs. "
                + "This suggests that the colorized paper failed to compile. Hues "
                + "will not be searched for in this diff directory.",
                diff_images_file_path,
            )
            return None

        for img_name in os.listdir(diff_images_file_path):
            img_path = os.path.join(diff_images_file_path, img_name)
            page_image = cv2.imread(img_path)

            if contains_black_pixels(page_image):
                logging.warning("Black pixels found in image diff %s", img_path)
                black_pixels_found = True

            page_number = int(os.path.splitext(img_name)[0].replace("page-", "")) - 1
            page_images[page_number] = page_image

        for entity_id, hue in entity_hues.items():
            for page_number, image in page_images.items():
                boxes = extract_bounding_boxes(image, page_number, hue)
                for box in boxes:
                    entity_locations[entity_id].append(box)

    return LocationResult(
        locations=entity_locations,
        shifted_entities=[],
        first_shifted_entity=None,
        black_pixels_found=black_pixels_found,
    )


def contains_black_pixels(img: np.ndarray) -> bool:

    # Black pixels will have value and saturation near 0. Still consider pixels with
    # a value above 0 because of aliasing in images, where black letters in an image
    # may appear as a group of grey pixels.
    SATURATION_THRESHOLD = 20  # out of 255
    VALUE_THRESHOLD = 150  # out of 255

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return bool(
        np.any(
            np.logical_and(
                img_hsv[:, :, 1] < SATURATION_THRESHOLD,
                img_hsv[:, :, 2] < VALUE_THRESHOLD,
            )
        )
    )

def has_hue_shifted(
    before: np.ndarray, after: np.ndarray, hue: float, tolerance: float = 0.02
) -> bool:
    """
    Detect whether pixels of a specified 'hue' have shifted away from where pixels were in a
    baseline image. Used to detect whether rasters of pages with colorized images had
    contain accidental layout changes. See 'extract_bounding_boxes' for a description of the 'hue'
    and 'tolerance' arguments.
    """

    CV2_MAXIMUM_HUE = 180

    # A pixel with a value above 230 and a saturation below 10 is considered blank.
    VALUE_THRESHOLD = 230  # out of 255
    SATURATION_THRESHOLD = 10  # out of 255

    # Detect which pixels in 'after' have changed from not filled to filled.
    before_hsv = cv2.cvtColor(before, cv2.COLOR_BGR2HSV)
    after_hsv = cv2.cvtColor(after, cv2.COLOR_BGR2HSV)

    SATURATION_CHANNEL = 1
    VALUE_CHANNEL = 2
    blank_before = np.logical_and(
        before_hsv[:, :, SATURATION_CHANNEL] < SATURATION_THRESHOLD,
        before_hsv[:, :, VALUE_CHANNEL] > VALUE_THRESHOLD,
    )
    blank_after = np.logical_and(
        after_hsv[:, :, SATURATION_CHANNEL] < SATURATION_THRESHOLD,
        after_hsv[:, :, VALUE_CHANNEL] > VALUE_THRESHOLD,
    )
    fill_changes = np.logical_xor(blank_before, blank_after)

    # Compute hues at all location where saturation changed.
    HUE_CHANNEL = 0
    after_hues = after_hsv[:, :, HUE_CHANNEL]

    # Determine whether the hue at any of the locations matches the input hue.
    cv2_hue = hue * CV2_MAXIMUM_HUE
    cv2_tolerance = tolerance * CV2_MAXIMUM_HUE
    distance_to_hue = np.abs(after_hues.astype(np.int16) - cv2_hue)
    abs_distance_to_hue = np.minimum(distance_to_hue, CV2_MAXIMUM_HUE - distance_to_hue)
    return np.any((abs_distance_to_hue <= cv2_tolerance) & fill_changes)