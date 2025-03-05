import re
class Robot_info: 
    """
    This code snippet defines a constructor function for a Python class. 
    The constructor initializes several attributes of the class, including dictionaries and lists. 
    Specifically, known_dict and obj_width_dict are empty dictionaries, current_loc is a list containing a single tuple, and grabbed_objects and openned_containers are empty lists. 
    Additionally, it sets up URLs for two APIs and a local file path.
    """
    def __init__(self):
        self.known_dict = {} # known_dict is a dictionary that stores the locations of known objects
        self.obj_width_dict = {} # obj_width_dict is a dictionary that stores the width of known objects
        self.current_loc = [(1, 1, 1)] # current_loc is a list that stores the current location of the robot
        self.grabbed_objects = [] # grabbed_objects is a list that stores the names of the objects that have been grabbed
        self.openned_containers = [] # openned_containers is a list that stores the names of the containers that have been opened

        self.PRE_LOCATE_OBJECT_API = "http://127.0.0.1:9999/" # PRE_LOCATE_OBJECT_API is the URL of the API that locates objects in the image.
        self.threshold = 0.4 # threshold is the confidence threshold for the grounded sam API

        self.Langchain_chatchat_API = "http://127.0.0.1:7861/" 
        self.Langchain_chatchat_embedding_Path = r"C:\Users\MSI\Desktop\langchain\Langchain-Chatchat\embeddings\embedding_keywords.txt"
        self.Local_Path = (
            "C:\\Users\\MSI\\Grounded-Segment-Anything\\previous_llm_yyq\\"
        )


robot_info = Robot_info()
