import sababox
import _thread

sb = sababox.SabaBox()
sb.init()
#_thread.start_new_thread('SabaBox', sb.start, ())
sb.start()
