const action_log = {};

function voteHover(reference) {
    let path = reference.getAttribute('href');
    let like_button = reference.childNodes[3];
    let dislike_button = reference.childNodes[1];

    if(path in action_log) {
        let state = action_log[path];

        if(state === 'like') {
            if(!like_button.classList.contains('voted')) {
                like_button.classList.add('voted');
            }
            dislike_button.classList.remove('voted');
            console.log('liked');
        } else if(state === 'dislike') {
            if(!dislike_button.classList.contains('voted')) {
                dislike_button.classList.add('voted');
            }
            like_button.classList.remove('voted');
            console.log('disliked');
        }
    } else {
        like_button.classList.remove('voted');
        dislike_button.classList.remove('voted');
        console.log('nothing');
    }

}

function voteClick(reference, action_type) {
    let path = reference.getAttribute('href');
    let overwrite = 'overwrite=';
    let action = 'action=';
    let http = new XMLHttpRequest();

    if (path in action_log) {
        overwrite += 'True';
        if(action_type === action_log[path]) {
            delete action_log[path];
            action += 'None';
        } else {
            action_log[path] = action_type;
            action += action_type;
        }

        voteHover(reference);
    } else {
            overwrite += 'False';
            action_log[path] = action_type;
            action += action_type;
            voteHover(reference);

    }

    http.open("POST", path);
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    http.send(action + '&' + overwrite);
    http.onreadystatechange = (e) => {
        console.log('done');
        console.log(http.responseText);
    }

}

function dev(reference) {
    console.log(reference)

}

function dev2(reference) {
    reference.classList.remove('voted')
    console.log(reference)
}

