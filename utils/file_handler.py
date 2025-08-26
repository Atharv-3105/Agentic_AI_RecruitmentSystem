import fitz
import docx
import pytesseract
from PIL import Image
import io


#=============Function To Extract Text from PDF================
def extract_text_from_pdf(file_bytes: bytes)-> str:
    ''' 
        This function will Extract text from the uploaded Resume PDF
        Input(Args):
                - Bytes of PDF File
        
        Output:
                - A string containing all the text from the Resume PDF 
    '''
    
    text = ""
    try:
        #Open the PDF 
        pdf_document = fitz.open(stream = file_bytes, filetype="pdf")
        
        for page_num in range(len(pdf_document)):
            text += pdf_document.load_page(page_num).get_text()

        #If text is minimal, Use OCR
        if(len(text.strip()) < 100):
             #Reset the text
             text = ""
             for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                #Convert page to an image
                pix = page.get_pixmap(dpi = 300)
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                
                #Extract the text from Image using OCR
                text += pytesseract.image_to_string(image)
        pdf_document.close()
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return ""

#==============Function to Extract Text from DOCX format Resume===========
def extract_text_from_docx(file_bytes: bytes)->str:
    ''' 
        This function will extract text from resumes uploaded in DOCX format
    '''
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([para.text for para in document.paragraphs]).strip()
    except Exception as e:
        print(f"Error processing DOCX file: {e}")
        return ""


#================Function to Extract text from Image format Resume===========
def extract_text_from_image(file_bytes: bytes) ->str:
    ''' 
        Extracts text from an image file using OCR.
    '''
    try:
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()
    except Exception as e:
        print(f"Error processing image file: {e}")
        return ""
                    

            