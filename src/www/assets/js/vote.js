function _update_vote(reference) {
    let children, thumbs_down, thumbs_up, http, course

    children = reference.childNodes
    thumbs_down = children[1]
    thumbs_up = children[3]
    course = reference.getAttribute('value')

    http = new XMLHttpRequest();
    http.onreadystatechange = (f) => {
        if (http.readyState === 4 && http.status === 200) {
            thumbs_down.classList.remove('voted')
            thumbs_up.classList.remove('voted')

            let rating = http.responseText

            if (rating === "\"dislike\"") {
                thumbs_down.classList.add('voted')
            } else if (rating === "\"like\"") {
                thumbs_up.classList.add('voted')
            }
        }
    }

    http.open("GET", '/rating?id=' + course);
    http.send();

}

function get_vote(reference) {
    let children = reference
        .childNodes[1]
        .childNodes[1]
        .childNodes[3]

    _update_vote(children)

}

function vote(reference, rating) {
    let course, children, thumbs_down, thumbs_up, http
    course = reference.getAttribute('value')
    children = reference.childNodes
    thumbs_down = children[1]
    thumbs_up = children[3]

    http = new XMLHttpRequest()
    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            location.reload()
        }
    }
    http.open("POST", '/rating')
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    http.send('cid=' + course + '&value=' + rating)

}


