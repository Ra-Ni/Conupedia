
function get_course(reference) {
    let course = reference.value
    let code = document.getElementById("code")
    let title = document.getElementById("title")
    let degree = document.getElementById("degree")
    let credits = document.getElementById("credits")
    let requisites = document.getElementById("requisites")
    let description = document.getElementById("description")
    let course_id = document.getElementById("course_id")
    course_id.value = course

    let http = new XMLHttpRequest();
    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            let response = JSON.parse(http.responseText)
            code.value = response['code']
            title.value = response['title']
            degree.value = response['degree']
            credits.value = response['credits']
            if ('requisites' in response) {
                requisites.value = response['requisites']
            }
            if ('description' in response) {
                description.value = response['description']
            }
        }
    }

    http.open("GET", '/course?id=' + course)
    http.send()
}

function search_table() {
    let input, filter, table, tr, td, i, txtValue

    input = document.getElementById("input")
    filter = input.value.toUpperCase()
    table = document.getElementById("table")
    tr = table.getElementsByTagName("button")

    for (i = 0; i < tr.length; i++) {
        td = tr[i]
        if (td) {
            txtValue = td.textContent || td.innerText
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].parentElement.style.display = ""
            } else {
                tr[i].parentElement.style.display = "none"
            }
        }
    }
}

function _search_course(name) {
    let i, td, table, buttons, txtValue, filter

    table = document.getElementById("table")
    filter = name.toUpperCase()
    buttons = table.getElementsByTagName("button")

    for (i = 0; i < buttons.length; i++) {
        td = buttons[i]
        if (td) {
            txtValue = td.textContent || td.innerText
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                return buttons[i].parentElement
            }
        }
    }
}

function delete_course() {
    let course_id, code, title, name, http, ele

    http = new XMLHttpRequest()
    course_id = document.getElementById('course_id')
    code = document.getElementById("code")
    title = document.getElementById("title")

    course_id = course_id.value
    name = code.value + ' - ' + title.value
    http.onreadystatechange = () => {
        if (http.readyState === 4 && http.status === 200) {
            ele = _search_course(name)
            ele.remove()

        }
    }
    http.open('DELETE', '/course/' + course_id)
    http.send()

}

function modify_course() {
    let params, buffer, http, body

    params = {}
    buffer = []
    params['course_id'] = document.getElementById('course_id').value
    params['code'] = document.getElementById("code").value
    params['title'] = document.getElementById("title").value
    params['credit'] = document.getElementById("credits").value
    params['degree'] = document.getElementById("degree").value
    params['requisites'] = document.getElementById("requisites").value
    params['description'] = document.getElementById("description").value
    http = new XMLHttpRequest()
    http.onreadystatechange = () => {}

    for(const k in params) {
        buffer.push(k + '=' + encodeURIComponent(params[k]))
    }

    body = buffer.join('&')

    http.open('POST', '/course')
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    http.send(body)


}