import os


class MediaTools:

    def image_info(self, path):
        try:
            from PIL import Image
            img = Image.open(path)
            return {'format': img.format, 'size': img.size,
                    'mode': img.mode, 'path': path}
        except ImportError:
            return {'error': 'Pillow not available'}
        except Exception as e:
            return {'error': str(e)}

    def convert_image(self, src, dst, format):
        try:
            from PIL import Image
            img = Image.open(src)
            img.save(dst, format=format)
            return {'success': True, 'path': dst}
        except ImportError:
            return {'error': 'Pillow not available'}
        except Exception as e:
            return {'error': str(e)}

    def video_info(self, path):
        return {'error': 'Video processing requires ffprobe or moviepy'}

    def audio_info(self, path):
        try:
            size = os.path.getsize(path)
            return {'path': path, 'size_bytes': size,
                    'format': os.path.splitext(path)[1].lstrip('.')}
        except Exception as e:
            return {'error': str(e)}


def run(action, **kwargs):
    mt = MediaTools()
    method = getattr(mt, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
