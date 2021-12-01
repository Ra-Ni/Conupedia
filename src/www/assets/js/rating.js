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