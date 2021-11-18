def to_html(course: str, description: str, partof: str, credits: str):
    return """   
    <li>

        <a class="uk-link-reset">
            <div class="bg-white shadow-sm rounded-lg uk-transition-toggle">


                <div class="w-full h-40 overflow-hidden rounded-t-lg relative">
                    <img src= " {{ url_for('web', path='assets/images/courses/img-1.jpg') }} "  alt="" class="w-full h-full absolute inset-0 object-cover">
                    <button>
                        <img src= " {{ url_for('web', path='assets/images/icon-dislike.svg') }} "  class="w-8 h-8 uk-position-bottom-right uk-transition-fade" alt="">
                    </button>
                    <button>
                        <img src= " {{ url_for('web', path='assets/images/icon-like.svg') }} "  class="w-8 h-8 uk-position-bottom-left uk-transition-fade" alt="">
                    </button>
                </div>
                <div class="p-4">
                    <div class="font-semibold line-clamp-2"> %s </div>
                    <div class="flex space-x-2 items-center text-sm pt-3">
                        <div> %s </div>

                    </div>
                    <div class="pt-1 flex items-center justify-between">
                        <div class="text-sm font-semibold"> %s </div>
                        <div class="text-lg font-semibold"> Credits:%s </div>
                    </div>
                </div>
            </div>
        </a>

    </li>
    """ % (course, description, partof, credits)
