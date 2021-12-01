function new_course_obj(course) {
        //Cover Image
        let cover_image = document.createElement('img')
        cover_image.setAttribute('src', 'http://127.0.0.1/assets/images/Concordia-card.png')
        cover_image.setAttribute('alt', '')
        cover_image.setAttribute('class', 'w-full h-full absolute inset-0 object-cover')

        //Thumbs
        let thumbs_down = document.createElement('img')
        //thumbs_down.setAttribute('onclick', 'vote(' + course.id + ', \'dislike\')')
        thumbs_down.addEventListener('click', function() {console.log('dislike')})
        thumbs_down.setAttribute('src', 'http://127.0.0.1/assets/images/thumbs-down.svg')
        thumbs_down.setAttribute('class', 'w-5 h-5 uk-position-bottom-right uk-transition-fade')
        thumbs_down.setAttribute('alt', '')
        let thumbs_up = document.createElement('img')
        //thumbs_up.setAttribute('onclick', 'vote(' + course.id + ', \'like\')')
        thumbs_up.setAttribute('src', 'http://127.0.0.1/assets/images/thumbs-up.svg')
        thumbs_up.setAttribute('class', 'w-5 h-5 uk-position-bottom-left uk-transition-fade')
        thumbs_up.setAttribute('alt', '')
        let thumbs_containers = document.createElement('button')
        thumbs_containers.appendChild(thumbs_down)
        thumbs_containers.appendChild(thumbs_up)

        //Cover
        let card_cover = document.createElement('div')
        card_cover.setAttribute('class', 'uk-card-media-top w-full h-20 overflow-hidden rounded-t-lg relative')
        card_cover.appendChild(cover_image)
        card_cover.appendChild(thumbs_containers)


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

        let card = document.createElement('a')
        card.setAttribute('class', 'uk-card uk-link-reset')
        card.setAttribute('onmouseenter', 'get_vote(' + course.id + ')')
        card.appendChild(card_container)

        let result = document.createElement('div')
        result.appendChild(card)

        return result
}

function load_course(container, id) {
        let response, http

        http = new XMLHttpRequest()
        http.onreadystatechange = () => {
                if (http.readyState === 4 && http.status === 200) {
                        response = JSON.parse(http.responseText)
                        response = new_course_obj(response)
                        container.appendChild(response)
                        console.log(response)
                }
        }
        http.open('GET', '/courses3?id=' + id)
        http.send()
}

function load_courses(container, courses) {
        let i
        for(i = 0 ; i < courses.length; i++) {
                load_course(container, courses[i].id)
        }
}



