
function _update(reference) {
    let children = reference.childNodes
    let thumbs_down = children[1]
    let thumbs_up = children[3]
    let http = new XMLHttpRequest();
    let course = reference.getAttribute('value')

    http.open("GET", '/rating?id=' + course);
    http.send();
    thumbs_down.classList.remove('voted')
    thumbs_up.classList.remove('voted')
    http.onreadystatechange = (f) => {
        let rating  = http.responseText;

        if (rating === "\"dislike\"") {
            thumbs_down.classList.add('voted')
        } else if (rating === "\"like\"") {
            thumbs_up.classList.add('voted')
        }
    }

}

function getVote(reference) {
    let children = reference
        .childNodes[1]
        .childNodes[1]
        .childNodes[3]

    _update(children)

}

function vote(reference, rating) {
    let course = reference.getAttribute('value')
    let children = reference.childNodes
    let thumbs_down = children[1]
    let thumbs_up = children[3]
    let http = new XMLHttpRequest();
    http.open("POST", '/rating');
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    http.send('cid=' + course + '&value=' + rating);

    http.onreadystatechange = (e) => {

        // _update(reference)
        location.reload()

    }





}
