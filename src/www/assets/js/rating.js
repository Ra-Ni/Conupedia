
function rate(rating) {
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