import bm4d
import numpy as np
import nibabel as nib
from skimage.util import view_as_blocks


def fix_image_orientation(image, axes, orientation='FFS'):
    """
    Adjusts the orientation of a 3D image array to match standard anatomical planes
    (sagittal, coronal, or transversal) and returns the oriented image along with labeling
    and metadata for visualization.

    Args:
        image (np.ndarray): A 3D numpy array representing the image data to be reoriented.
        axes (list[int]): A list of three integers representing the current order of the
                          axes in the image (e.g., [0, 1, 2] for x, y, z).

    Returns:
        output (dict): A dictionary containing the following keys:
            - 'widget': A fixed string "image" or "curve" indicating the type of data for visualization.
            - 'data': The reoriented 3D image array (np.ndarray).
            - 'xLabel': A string representing the label for the x-axis in the visualization.
            - 'yLabel': A string representing the label for the y-axis in the visualization.
            - 'title': A string representing the title of the visualization (e.g., "Sagittal").
        image (np.ndarray): Reoriented 3D image array
        dicom_orientation (list): orientation for dicom file
    """

    # Get axes in strings
    axes_dict = {'x': 0, 'y': 1, 'z': 2}
    axes_keys = list(axes_dict.keys())
    axes_vals = list(axes_dict.values())
    axes_str = ['', '', '']
    n = 0
    for val in axes:
        index = axes_vals.index(val)
        axes_str[n] = axes_keys[index]
        n += 1

    # Create output dictionaries to plot figures
    x_label = "%s axis" % axes_str[1]
    y_label = "%s axis" % axes_str[0]
    title = "Image"
    if axes[2] == 2:  # Sagittal
        title = "Sagittal"
        if axes[0] == 0 and axes[1] == 1:
            image = np.flip(image, axis=0)
            x_label = "(-Y) A | PHASE | P (+Y)"
            y_label = "(-X) I | READOUT | S (+X)"
        else:
            image = np.transpose(image, (0, 2, 1))
            image = np.flip(image, axis=0)
            x_label = "(-Y) A | READOUT | P (+Y)"
            y_label = "(-X) I | PHASE | S (+X)"
        image_orientation_dicom = [0.0, 1.0, 0.0, 0.0, 0.0, -1.0]
    elif axes[2] == 1:  # Coronal
        title = "Coronal"
        if axes[0] == 0 and axes[1] == 2:
            x_label = "(+Z) R | PHASE | L (-Z)"
            y_label = "(-X) I | READOUT | S (+X)"
        else:
            image = np.transpose(image, (0, 2, 1))
            x_label = "(+Z) R | READOUT | L (-Z)"
            y_label = "(-X) I | PHASE | S (+X)"
        image_orientation_dicom = [1.0, 0.0, 0.0, 0.0, 0.0, -1.0]
    elif axes[2] == 0:  # Transversal
        title = "Transversal"
        if axes[0] == 1 and axes[1] == 2:
            image = np.flip(image, axis=0)
            x_label = "(+Z) R | PHASE | L (-Z)"
            y_label = "(+Y) P | READOUT | A (-Y)"
        else:
            image = np.transpose(image, (0, 2, 1))
            image = np.flip(image, axis=0)
            x_label = "(+Z) R | READOUT | L (-Z)"
            y_label = "(+Y) P | PHASE | A (-Y)"
        image_orientation_dicom = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    output = {
        'widget': 'image',
        'data': image,
        'xLabel': x_label,
        'yLabel': y_label,
        'title': title,
    }

    return output, image, image_orientation_dicom

def save_nifti(axes_orientation, n_points, fov, dfov, image, file_path):
    axes_orientation = np.array(axes_orientation)
    n_xyz = [0, 0, 0]
    reorder = [0, 0, 0]
    for i, axis in enumerate(axes_orientation):
        n_xyz[axis] = n_points[i]
        reorder[axis] = i
    fov = np.array(fov)  # cm
    dfov = np.array(dfov)  # mm
    resolution = fov / n_xyz * 10  # mm
    image = np.transpose(image, axes=(2, 1, 0))
    image = np.transpose(image, reorder)
    image = np.transpose(image, axes=(2, 1, 0))
    image = image[::-1, ::-1, ::-1]
    image = image / np.max(image)

    orientation = 'FFS'

    # Create afine matrix
    if orientation == 'FFS':
        affine = np.zeros((4, 4))
        affine[0, 0] = resolution[2]
        affine[1, 1] = resolution[1]
        affine[2, 2] = resolution[0]
        affine[0, 3] = dfov[2]
        affine[1, 3] = - dfov[1]
        affine[2, 3] = dfov[0]
        affine[3, 3] = 1
    elif orientation == 'HFS':
        print("Affine matrix not ready.")
    elif orientation == 'FFP':
        print("Affine matrix not ready.")
    elif orientation == 'HFP':
        print("Affine matrix not ready.")

    # Create the NIfTI image
    nifti_img = nib.Nifti1Image(np.abs(image), affine)

    # Save the NIfTI file
    nib.save(nifti_img, file_path)

def run_cosbell_filter(sampled, data, cosbell_order):
    """
    Apply the Cosbell filter operation to the k-space data along three directions.

    This method applies the Cosbell filter to the k-space data along the readout ('rd'), phase ('ph'), and slice
    ('sl') directions. It modifies the input k-space data in-place.

    Args:
        sampled (ndarray): The sampled k-space coordinates in a nx3 matrix, where n is the number of points in k-space. The three columns correspond to the readout, phase, and slice directions.
        data (ndarray): The 3D matrix representing the k-space data to be filtered (sl, ph, rd).
        cosbell_order (list): The order of the Cosbell filter for each direction (rd, ph, sl)

    Returns:
        ndarray: The filtered k-space data (sl, ph, rd).
    """
    n_points = data.shape

    # Along readout
    k = np.reshape(sampled[:, 0], n_points)
    kmax = np.max(np.abs(k[:]))
    theta = k / kmax
    data *= (np.cos(theta * (np.pi / 2)) ** cosbell_order[0])

    # Along phase
    k = np.reshape(sampled[:, 1], n_points)
    kmax = np.max(np.abs(k[:]))
    theta = k / kmax
    data *= (np.cos(theta * (np.pi / 2)) ** cosbell_order[1])

    # Along slice
    k = np.reshape(sampled[:, 2], n_points)
    kmax = np.max(np.abs(k[:]))
    theta = k / kmax
    data *= (np.cos(theta * (np.pi / 2)) ** cosbell_order[2])

    return data

def run_bm4d_filter(image_data, std=0):
    """
    Apply the BM4D filter to denoise the image.

    This method retrieves the image data, rescales it, calculates the standard deviation for the BM4D filter,
    applies the BM4D filter to denoise the rescaled image, and rescales the denoised image back to its original
    scale.

    Args:
        image_data (ndarray): The input image data.
        std (float): standard deviation for bm4d. If zero, the standard deviation will be calculated automatically. Default 0

    Returns:
        ndarray: The denoised image.

    """
    # Rescale the image data for processing
    reference = np.max(image_data)
    image_rescaled = image_data / reference * 100

    # Calculate the standard deviation for BM4D filter
    if std==0:
        # Quantize image
        num_bins = 1000
        image_quantized = np.digitize(image_rescaled, bins=np.linspace(0, 1, num_bins + 1)) - 1

        # Divide the image into blocks
        n_multi = (np.array(image_quantized.shape) / 5).astype(int) * 5
        blocks_r = view_as_blocks(image_rescaled[0:n_multi[0], 0:n_multi[1], 0:n_multi[2]], block_shape=(5, 5, 5))

        # Calculate the standard deviation for each block
        block_std_devs = np.std(blocks_r, axis=(3, 4, 5))

        # Calculate the average value for each block
        block_mean = np.mean(blocks_r, axis=(3, 4, 5))

        # Find the indices of the block with the minimum mean
        min_mean_index = np.unravel_index(np.argmin(block_mean), block_mean.shape)

        # Extract the block with the highest entropy from the block_std_devs array
        std = 4 * block_std_devs[min_mean_index]
        print("Standard deviation for BM4D: %0.2f" % std)

    # Create a BM4D profile and set options
    profile = bm4d.BM4DProfile()
    stage_arg = bm4d.BM4DStages.ALL_STAGES
    blockmatches = (False, False)

    # Apply the BM4D filter to the rescaled image
    denoised_rescaled = bm4d.bm4d(image_rescaled, sigma_psd=5, profile=profile, stage_arg=stage_arg,
                                  blockmatches=blockmatches)

    # Rescale the denoised image back to its original dimensions
    denoised_image = denoised_rescaled / 100 * reference

    return denoised_image

def run_dfft(image):
    """
    Perform direct FFT reconstruction.

    This method performs the direct Fourier transform to obtain the k-space data from an image in the spatial
    domain.

    Args:
        image (ndarray): The image in the spatial domain (sl, ph, rd).

    Returns:
        ndarray: The k-space data.

    """
    k_space = np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(image)))
    return k_space

def run_ifft(k_space):
    """
    Perform inverse FFT reconstruction.

    This method performs the inverse Fourier transform to reconstruct the image in the spatial domain from k-space
    data.

    Args:
        k_space (ndarray): The k-space data (sl, ph, rd).

    Returns:
        ndarray: The reconstructed image in the spatial domain.

    """
    image = np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(k_space)))
    return image

def run_zero_padding(k_space, new_size):
    """
    Perform zero-padding on the given k-space data.

    This function retrieves the desired zero-padding dimensions from the user input,
    creates a new k-space matrix with the specified size filled with zeros, and places
    the original k-space data at the center of the new matrix. It ensures that the
    k-space is properly centered even if the new dimensions are larger or smaller
    than the original.

    Parameters:
    -----------
    k_space : np.ndarray
        A 3D complex-valued NumPy array representing the original k-space data.
    new_size: list
        A list with the new matrix size (rd, ph, sli)

    Returns:
    --------
    np.ndarray
        A 3D complex-valued NumPy array containing the new k-space data.

    Notes:
    ------
    - The function calculates the appropriate offsets to center the original k-space
      within the new zero-padded matrix.
    - If the new matrix size is smaller in any dimension, it crops the k-space accordingly.
    """
    # Get the k_space shape
    shape_0 = k_space.shape

    # Determine the new shape after zero-padding
    n_rd = int(new_size[0])
    n_ph = int(new_size[1])
    n_sl = int(new_size[2])
    shape_1 = n_sl, n_ph, n_rd

    # Create an image matrix filled with zeros
    image_matrix = np.zeros(shape_1, dtype=complex)

    # Calculate the centering offsets for each dimension
    offset_0 = (shape_1[0] - shape_0[0]) // 2
    offset_1 = (shape_1[1] - shape_0[1]) // 2
    offset_2 = (shape_1[2] - shape_0[2]) // 2

    # Calculate the start and end indices to center the k_space within the new image_matrix
    new_start_0 = offset_0 if offset_0 >= 0 else 0
    new_start_1 = offset_1 if offset_1 >= 0 else 0
    new_start_2 = offset_2 if offset_2 >= 0 else 0
    new_end_0 = new_start_0 + shape_0[0] if offset_0 > 0 else shape_1[0]
    new_end_1 = new_start_1 + shape_0[1] if offset_1 > 0 else shape_1[1]
    new_end_2 = new_start_2 + shape_0[2] if offset_2 > 0 else shape_1[2]

    # Calculate the start and end indices of old matrix
    old_start_0 = 0 if offset_0 >= 0 else -offset_0
    old_start_1 = 0 if offset_1 >= 0 else -offset_1
    old_start_2 = 0 if offset_2 >= 0 else -offset_2
    old_end_0 = shape_0[0] if offset_0 >= 0 else old_start_0 + shape_1[0]
    old_end_1 = shape_0[1] if offset_1 >= 0 else old_start_1 + shape_1[1]
    old_end_2 = shape_0[2] if offset_2 >= 0 else old_start_2 + shape_1[2]

    # Copy the k_space into the image_matrix at the center
    image_matrix[new_start_0:new_end_0, new_start_1:new_end_1, new_start_2:new_end_2] = k_space[
                                                                                        old_start_0:old_end_0,
                                                                                        old_start_1:old_end_1,
                                                                                        old_start_2:old_end_2
                                                                                        ]

    return image_matrix

def hanning_filter(kSpace, mm, nb_point):
    """
    Apply a Hanning filter to the k-space data.

    Args:
        kSpace (ndarray): K-space data.
        n (int): Number of zero-filled points in k-space.
        m (int): Number of acquired points in k-space.
        nb_point (int): Number of points before m+n where reconstruction begins to go to zero.

    Returns:
        ndarray: K-space data with the Hanning filter applied.
    """
    kSpace_hanning = np.copy(kSpace)
    kSpace_hanning[mm[0]::, :, :] = 0.0
    kSpace_hanning[:, mm[1]::, :] = 0.0
    kSpace_hanning[:, :, mm[2]::] = 0.0

    # Calculate the Hanning window
    hanning_window = np.hanning(nb_point * 2)
    hanning_window = hanning_window[int(len(hanning_window)/2)::]

    if not mm[0] == np.size(kSpace, 0):
        for ii in range(nb_point):
            kSpace_hanning[mm[0]-nb_point+ii+1, :, :] *= hanning_window[ii]
    if not mm[1] == np.size(kSpace, 1):
        for ii in range(nb_point):
            kSpace_hanning[:, mm[1]-nb_point+ii+1, :] *= hanning_window[ii]
    if not mm[2] == np.size(kSpace, 2):
        for ii in range(nb_point):
            kSpace_hanning[:, :, mm[2]-nb_point+ii+1] *= hanning_window[ii]

    return kSpace_hanning

def run_pocs_reconstruction(n_points, factors, k_space_ref):
    """
    Perform POCS reconstruction.

    Retrieves the number of points before m+n where reconstruction begins to go to zero.
    Retrieves the correlation threshold for stopping the iterations.
    Computes the partial image and full image for POCS reconstruction.
    Applies the iterative reconstruction with phase correction.
    Updates the main matrix of the image view widget with the interpolated image.
    Adds the "POCS" operation to the history widget and updates the history dictionary and operations history.
    """

    def getCenterKSpace(k_space, m_vec):
        # fix n_vec
        output = np.zeros(np.shape(k_space), dtype=complex)
        n_vec = np.array(np.shape(k_space))

        # fill with zeros
        idx0 = n_vec // 2 - m_vec
        idx1 = n_vec // 2 + m_vec
        output[idx0[0]:idx1[0], idx0[1]:idx1[1], idx0[2]:idx1[2]] = \
            k_space[idx0[0]:idx1[0], idx0[1]:idx1[1], idx0[2]:idx1[2]]

        return output

    # Get n and m
    factors = [float(num) for num in factors][-1::-1]
    mm = np.array([int(num) for num in (n_points * factors)])
    m = np.array([int(num) for num in (n_points * factors - n_points / 2)])

    # Get the reference image
    img_ref = np.abs(run_ifft(k_space_ref))

    # Create a copy with the center of k-space
    k_space_center = getCenterKSpace(k_space_ref, m)

    # Number of points before m+n where we begin to go to zero
    nb_point = 2

    # Set the correlation threshold for stopping the iterations
    threshold = 1e-6

    # Get image phase
    img_center = run_ifft(k_space_center)
    phase = img_center / abs(img_center)

    # Generate the corresponding image with the Hanning filter
    k_space_hanning = hanning_filter(k_space_ref, mm, nb_point)
    img_hanning = np.abs(run_ifft(k_space_hanning))

    num_iterations = 0  # Initialize the iteration counter
    previous_img = img_hanning.copy()  # you have the choice between img_hanning or img_ramp

    while True:
        # Iterative reconstruction
        img_iterative = previous_img * phase
        k_space_new = run_dfft(img_iterative)

        # Apply constraint: Keep the region of k-space from n+m onwards and restore the rest
        k_space_new[0:mm[0], 0:mm[1], 0:mm[2]] = k_space_ref[0:mm[0], 0:mm[1], 0:mm[2]]

        # Reconstruct the image from the modified k-space
        img_reconstructed = np.abs(run_ifft(k_space_new))

        # Compute correlation between consecutive reconstructed images
        correlation = np.corrcoef(previous_img.flatten(), img_reconstructed.flatten())[0, 1]

        # Display correlation and current iteration number
        print("Iteration: %i, Convergence: %0.2e" % (num_iterations, (1-correlation)))

        # Check if correlation reaches the desired threshold
        if (1-correlation) <= threshold or num_iterations >= 100:
            break

        # Update previous_img for the next iteration
        previous_img = img_reconstructed.copy()

        # Increment the iteration counter
        num_iterations += 1

    # Get correlation with reference image
    correlation = np.corrcoef(img_ref.flatten(), img_reconstructed.flatten())[0, 1]
    print("Respect the reference image:")
    print("Convergence: %0.2e" % (1 - correlation))

    return img_reconstructed