
function new_course_obj(course) {
    //Cover Image
    let cover_image = document.createElement('img')
    cover_image.setAttribute('src', '/assets/images/Concordia-card.png')
    cover_image.setAttribute('alt', '')
    cover_image.setAttribute('class', 'w-full h-full absolute inset-0 object-cover')

    /*************************************** THUMBS ***************************************/
    let thumbs_down_icon, thumbs_up_icon, thumbs_down, thumbs_up
    //
    // thumbs_down_icon = document.createElement('i')
    // thumbs_down_icon.setAttribute('data-feather', 'thumbs-down')
    thumbs_down_icon = document.createElement('img')
    thumbs_down_icon.setAttribute('src', 'assets/images/thumbs-down.svg')
    //thumbs_up_icon = document.createElement('i')
    //thumbs_up_icon.setAttribute('data-feather', 'thumbs-up')
    thumbs_up_icon = document.createElement('img')
    thumbs_up_icon.setAttribute('src', 'assets/images/thumbs-up.svg')

    thumbs_down = document.createElement('button')
    thumbs_down.setAttribute('class', 'w-5 h-5 uk-position-bottom-right uk-transition-fade')
    thumbs_down.appendChild(thumbs_down_icon)
    thumbs_down.addEventListener('click', () => {
        post_rating(course.id, 'dislike', thumbs_down, thumbs_up)
    })

    thumbs_up = document.createElement('button')
    thumbs_up.setAttribute('class', 'w-5 h-5 uk-position-bottom-left uk-transition-fade')
    thumbs_up.appendChild(thumbs_up_icon)
    thumbs_up.addEventListener('click', () => {
        post_rating(course.id, 'like', thumbs_up, thumbs_down)
    })

    /**********************************************************************************/

    //Cover
    let card_cover = document.createElement('div')
    card_cover.setAttribute('class', 'uk-card-media-top w-full h-20 overflow-hidden rounded-t-lg relative')
    card_cover.appendChild(cover_image)
    card_cover.appendChild(thumbs_down)
    card_cover.appendChild(thumbs_up)


    let title = document.createElement('div')
    title.setAttribute('class', 'text-sm font-semibold line-clamp-2')
    title.textContent = course.code + ' - ' + course.title
    let title_container = document.createElement('div')
    title_container.setAttribute('style', 'height: 2rem')
    title_container.appendChild(title)

    let description = document.createElement('div')
    description.setAttribute('class', 'line-clamp-10')
    description.setAttribute('style', 'height: 10rem')
    description.textContent = course.description
    let description_container = document.createElement('div')
    description_container.setAttribute('class', 'flex space-x-2 items-center text-xs pt-4')
    description_container.appendChild(description)

    let degree = document.createElement('div')
    degree.setAttribute('class', 'text-sm font-semibold')
    degree.textContent = course.degree
    let credits = document.createElement('div')
    credits.setAttribute('class', 'text-sm font-semibold')
    credits.textContent = 'Credits: ' + course.credit
    let footer = document.createElement('div')
    footer.setAttribute('class', 'pt-1 flex items-center justify-between')
    footer.appendChild(degree)
    footer.appendChild(credits)

    let card_body = document.createElement('div')
    card_body.setAttribute('class', 'uk-card-body p-4 noselect')
    card_body.appendChild(title_container)
    card_body.appendChild(description_container)
    card_body.appendChild(footer)

    let card_container = document.createElement('div')
    card_container.setAttribute('class', 'bg-white shadow-sm rounded-lg uk-transition-toggle')
    card_container.appendChild(card_cover)
    card_container.appendChild(card_body)

    let card = document.createElement('div')
    card.appendChild(card_container)
    card.setAttribute('class', 'uk-card uk-link-reset')
    card.addEventListener('mouseenter', () => {
        get_rating(course.id, thumbs_up, thumbs_down)
    })

    let result = document.createElement('div')
    result.appendChild(card)


    return result
}

function load_course(container, id) {
    let response, http

    http = new XMLHttpRequest()
    http.cookie = document.cookie
    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            response = JSON.parse(http.responseText)
            response = new_course_obj(response)
            container.appendChild(response)
        }
    }
    http.open('GET', '/course?id=' + id)
    http.send()
}


function load_courses() {
    let http, container, courses, i, category

    category = document.getElementById('category')
    category = category.textContent
    category = category.toLowerCase()
    container = document.getElementById('container')

    http = new XMLHttpRequest()
    http.cookie = document.cookie
    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            courses = JSON.parse(http.responseText)
            for (i = 0; i < courses.length; i++) {
                load_course(container, courses[i].id)
            }

        }
    }

    http.open('GET', '/' + category)
    http.send()
}

function post_rating(course, rating, button, other) {
    let http
    http = new XMLHttpRequest()

    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            if (other.classList.contains('voted')) {
                other.classList.remove('voted')
            }
            button.classList.toggle('voted')
        }
    }
    http.open('POST', '/rating')
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    http.send('cid=' + course + '&value=' + rating)

}


function get_rating(id, thumbs_up, thumbs_down) {
    let http, response
    http = new XMLHttpRequest()

    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            response = JSON.parse(http.responseText)
            response = response['rating']

            if (response === 'like') {
                if (thumbs_down.classList.contains('voted')) {
                    thumbs_down.classList.remove('voted')
                }
                thumbs_up.classList.toggle('voted')
            } else if (response === 'dislike') {
                if (thumbs_up.classList.contains('voted')) {
                    thumbs_up.classList.remove('voted')
                }
                thumbs_down.classList.toggle('voted')
            }
        }
    }
    http.open('GET', '/rating?id=' + id)
    http.send()
}


let categories = ['recommendations', 'explore', 'latest', 'popular', 'likes']

categories.forEach(item => {
    let target = document.getElementById(item)
    target.onclick = () => {
        let category = document.getElementById('category')
        category.textContent = target.textContent
        container.innerHTML = ''
        load_courses()
    }
})

document.getElementById('logout').onclick = () => {
    let http = new XMLHttpRequest()
    http.onreadystatechange = () => {}
    http.open('GET', '/logout')
    http.send()
}


document.getElementById('back').setAttribute('--tw-text-opacity', '1')
document.getElementById('back').setAttribute('color', 'rgba(59,130,246,var(--tw-text-opacity))')