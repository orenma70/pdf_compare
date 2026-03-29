from fontTools.misc.cython import returns

print('++++++++++++++++++++++++++++++')

# This is a sample Python script.
# import os
from pathlib import Path
import numpy as np
# from matplotlib import pyplot as plt
from PIL import Image  # , ImageSequence
import fitz  # PyMuPDF
import argparse
import difflib


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text


def save_diff_as_pdf(diff_text, output_pdf_path):
    doc = fitz.open()  # Create a new PDF document
    page = doc.new_page()  # Add a blank page

    # Set font and write text
    text = "\n".join(diff_text)
    page.insert_text((50, 50), text, fontsize=10)  # Adjust position and size

    doc.save(output_pdf_path)
    doc.close()


def compare_pdfs(pdf1, pdf2, output_pdf):
    text1 = extract_text_from_pdf(pdf1).splitlines()
    text2 = extract_text_from_pdf(pdf2).splitlines()

    diff = difflib.unified_diff(text1, text2, lineterm="")
    save_diff_as_pdf(diff, output_pdf)
    print(f"Diff saved to {output_pdf}")


def read_images_from_pdf_using_fitz(pdf_path, start, stop, dpi=300):
    doc = fitz.open(pdf_path)
    binary_images = []
    # Ensure `stop` does not exceed the total number of pages
    stop = min(stop, len(doc))

    for i in range(start - 1, stop):
        pix = doc[i].get_pixmap(dpi=dpi)  # Render the page at specified DPI
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Convert to 1-bit image
        img_1bit = img.convert('1')  # Converts the image to 1-bit pixels
        binary_images.append(np.array(img_1bit))
    doc.close()
    return binary_images


def list_files_in_folder(folder_path,ftype1):
    try:
        # Get a list of all files and directories in the specified folder
        # files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        path = Path(folder_path)
        filesout = [file.name for file in path.iterdir() if file.is_file() and file.suffix == ftype1]
        return filesout
    except FileNotFoundError:
        print("Error: Folder not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []



TIFF_MODE = False  # Set to True to enable TIFF processing
# Example usage
old_path = r'C:\a\sag1\\'
new_path = r'C:\a\sag2\\'
dpi = 300

#compare_pdfs("C:\\a\\sag1\\A.pdf", "C:\\a\\sag2\\A.pdf", "difference.pdf")

if TIFF_MODE:
    ftype1 = '.tif'
else:
    ftype1 = '.pdf'

old_list = list_files_in_folder(old_path,ftype1)
new_list = list_files_in_folder(new_path,ftype1)

skip1 = 0
skip2 = 0
N = len(old_list)

for inx in range(N):

    olddoc = fitz.open(old_path + old_list[inx])
      # Render the page at specified DPI
    Np_old = olddoc.page_count
    TIFF_MODE = not olddoc.is_pdf
    newdoc = fitz.open(new_path + new_list[inx])
    #newpix = newdoc[1].get_pixmap(dpi=dpi)  # Render the page at specified DPI
    Np_new = newdoc.page_count

    if Np_new == Np_old:
        N_pages = Np_new
    else:
        print("Error: Pages don't match.")
        continue


    diffarray1 = []
    diffarray3 = []
    difflag = False
    print(old_list[inx])

    force_diff = False
    #Nfile = 196
    num_images = 0 # write 0 for start from the begining
    if force_diff:
        N_pages = num_images + 1

    #N_pages =20
    margin = 0
    # Loop through each frame in the TIFF file
    try:
        while num_images < N_pages:
            if TIFF_MODE:
                im_new.seek(num_images)  # Move to the next frame
                im_old.seek(num_images)  # Move to the next frame
                image_old = im_old.copy()
                image_new = im_new.copy()
                image_old = np.array(image_old.convert('1'), dtype=bool)
                image_new = np.array(image_new.convert('1'), dtype=bool)
                assert image_old.shape == image_new.shape, (f"Size of Image 5: {image_new.shape}, "
                                                        f"Size of Image 6: {image_old.shape}")
            else:
                im_old = read_images_from_pdf_using_fitz(old_path + old_list[inx],num_images,num_images,300) #im_old[num_images]
                im_new = read_images_from_pdf_using_fitz(new_path + new_list[inx],num_images,num_images,300) #im_new[num_images]

            image_old = im_old[0]
            image_new = im_new[0]

            height1, width1 = image_old.shape
            height2, width2 = image_new.shape

            #if width2>width1:
                # Crop first part: columns 0 to end-2 (i.e., exclude last column)
            part1 = image_old[:, 0+margin:width1-margin]

            # Crop second part: columns 2 to end-1 (i.e., skip the first two columns)
            part2 = image_new[:, 0+margin:width2-margin]

            # Now, compare these two parts
            diff = part1 ^ part2


            num_images += 1
            num_differing_pixels = np.sum(diff)

            if num_differing_pixels>0: #50000:
                difflag = True
                print(f'Page num {num_images} num_differing_pixels={num_differing_pixels} is NOT OK!!!')
                diff = np.logical_not(diff)

                concatenated_images = np.concatenate([image_old, image_new, diff], axis=1)

                # diff_image = Image.fromarray(concatenated_images.astype(np.uint8) * 255)

                # Convert to '1' mode image using Pillow
                diff_image3 = Image.fromarray(concatenated_images)
                diff_image1= Image.fromarray(diff)

                # Scale to 0 (black) and 255 (white)

                diffarray3.append(diff_image3)
                diffarray1.append(diff_image1)
            else:
                print(f'Page num {num_images} is OK.')

    except EOFError:  # End of file reached when there are no more frames
        pass

    if difflag:
        diff_path1 = rf'C:\a\diff\diff{inx + 1}_1.pdf'
        diff_path3 = rf'C:\a\diff\diff{inx + 1}_3.pdf'

        diffarray1[0].save(diff_path1, save_all=True, append_images=diffarray1[1:])
        diffarray3[0].save(diff_path3, save_all=True, append_images=diffarray3[1:])
