import functools as ft
import random    as rd
import streamlit as st
import streamlit.components.v1 as components

def InjectJs(js: str, atEveryRerun: bool = False) -> None:

    components.html("<script type='text/javascript'>\n" +
                    (f"// random number: {rd.random()}\n" if atEveryRerun else "") +
                    "element = Array.from(parent.document.getElementsByTagName('iframe'))" +
                    ".find(x => x.contentDocument == document).parentElement;\n" +
                    "element.style.display = 'none';\n" +
                    js + "\n</script>", 
                    height = 0)

def AddAttributes(*, id: str = None, cls: str = None, css: str = None) -> None:

    jsCode = ""

    if cls is not None:

        jsCode += f"element.previousElementSibling.classList.add('{cls}');\n"

    if id is not None:

        jsCode += f"element.previousElementSibling.id = '{id}';\n"

    InjectJs(jsCode, atEveryRerun = cls is not None)

    if css is not None:

        InjectCss(css.replace("#id", ("#" + id) or "#id"))

def InjectCss(css: str) -> None:

    id = "tw-" + str(hash(css))

    st.markdown("<style>#" + id + " { display: none; } " + css + "</style>", unsafe_allow_html = True)

    AddAttributes(id = id)

class Tweaker(type):

    def __getattr__(self, name):

        stFunc = getattr(st, name)

        @ft.wraps(stFunc)
        def newFunc(*args, id = None, cls = None, css = None, **kwargs):

            retVal = stFunc(*args, **kwargs)

            if cls is not None and callable(cls):

                cls = cls(retVal)

            if any([id, cls, css]):

                AddAttributes(id = id, cls = cls, css = css)

            return retVal
            
        return newFunc
     
class st_tweaker(metaclass = Tweaker):
    
    """Examples:
    
        # Custom HTML ID
        st_tweaker.text_input(label = 'Label', id = 'element-id')

        # Custom CSS
        st_tweaker.text_input(label = 'Label', id = 'element-id', css = '#element-id label p { font-size: 50px; }')

        # Custom static Class
        st_tweaker.text_input(label = 'Label', id = 'element-id', cls = 'green', css = '.green label p { color: green; }')

        # Custom Dynamic Class (Based on widget return value)
        st_tweaker.text_input(label = 'Label', id = 'element-id', cls = lambda value: 'green' if value == 'Hello!' else None, css = '.green label p { color: green; }')
    
    """