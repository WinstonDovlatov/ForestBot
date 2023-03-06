class Preprocessor:
    @staticmethod
    def preprocess(photo):
        return photo


class Postprocessor:
    @staticmethod
    def postprocess(original_img, mask):
        # apply threshold and combine
        return original_img.rotate(45)