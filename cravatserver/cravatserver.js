function openSubmitPage (username) {
    location.href = location.protocol + '//' + window.location.host + '/submit/index.html?username=' + username;
}

function openLoginPage () {
    location.href = location.protocol + '//' + window.location.host + '/server/login.html';
}

function login () {
    var usernameSubmit = document.getElementById('login_username').value;
    var passwordSubmit = document.getElementById('login_password').value;
    $.ajax({
        url: '/server/login',
        data: {'username':usernameSubmit, 'password':passwordSubmit},
        success: function (response) {
            if (response == 'success') {
                username = usernameSubmit;
                openSubmitPage(username);
            } else if (response == 'fail') {
                msgAccountDiv('Login failed');
            }
        }
    });
}

function logout () {
    $.ajax({
        url: '/server/logout',
        success: function (response) {
            openLoginPage();
        }
    });
}

function getPasswordQuestion () {
    var email = document.getElementById('forgotpasswordemail').value;
    $.ajax({
        url: '/server/passwordquestion',
        data: {'email': email},
        success: function (response) {
            var status = response['status'];
            var msg = response['msg'];
            if (status == 'fail') {
                msgAccountDiv(msg);
            } else {
                document.getElementById('forgotpasswordgetquestiondiv').style.display = 'none';
                document.getElementById('forgotpasswordquestion').textContent = msg;
                document.getElementById('forgotpasswordquestionanswerdiv').style.display = 'inline-block';
            }
        }
    });
}

function showSignupDiv () {
    document.getElementById('logindiv').style.display = 'none';
    document.getElementById('signupdiv').style.display = 'block';
}

function showLoginDiv () {
    document.getElementById('logindiv').style.display = 'block';
    document.getElementById('signupdiv').style.display = 'none';
    document.getElementById('forgotpassworddiv').style.display = 'none';
}

function submitForgotPasswordAnswer () {
    var email = document.getElementById('forgotpasswordemail').value;
    var answer = document.getElementById('forgotpasswordanswer').value;
    $.ajax({
        url: '/server/passwordanswer',
        data: {'email': email, 'answer': answer},
        success: function (response) {
            var success = response['success'];
            var msg = response['msg'];
            if (success == true) {
                document.getElementById('forgotpassworddiv').style.display = 'none';
                document.getElementById('forgotpasswordemail').textContent = '';
                document.getElementById('forgotpasswordquestion').textContent = '';
                document.getElementById('forgotpasswordanswer').textContent = '';
                alert('Password has been reset to ' + msg);
                showLoginDiv();
            } else {
                msgAccountDiv(msg);
            }
        }
    });
}

function forgotPassword () {
    document.getElementById('logindiv').style.display = 'none';
    document.getElementById('forgotpasswordquestion').textContent = '';
    document.getElementById('forgotpasswordgetquestiondiv').style.display = 'block';
    document.getElementById('forgotpasswordquestionanswerdiv').style.display = 'none';
    document.getElementById('forgotpassworddiv').style.display = 'block';
}

function changePassword () {
    var div = document.getElementById('changepassworddiv');
    var display = div.style.display;
    if (display == 'block') {
        display = 'none';
    } else {
        display = 'block';
    }
    div.style.display = display;
}

function submitNewPassword () {
    var oldpassword = document.getElementById('changepasswordoldpassword').value;
    var newpassword = document.getElementById('changepasswordnewpassword').value;
    var retypenewpassword = document.getElementById('changepasswordretypenewpassword').value;
    if (newpassword != retypenewpassword) {
        msgAccountDiv('New password mismatch');
        return;
    }
    $.ajax({
        url: '/server/changepassword',
        data: {'oldpassword': oldpassword,
               'newpassword': newpassword},
        success: function (response) {
            if (response == 'success') {
                msgAccountDiv('Password changed successfully.');
                document.getElementById('changepassworddiv').style.display = 'none';
            } else {
                msgAccountDiv(response);
            }
        }
    });
}

function hideloginsignupdiv () {
    document.getElementById('loginsignupdialog').style.display = 'none';
}

function toggleloginsignupdiv () {
    document.getElementById('logindiv').style.display = 'block';
    document.getElementById('signupdiv').style.display = 'none';
    var dialog = document.getElementById('loginsignupdialog');
    var display = dialog.style.display;
    if (display == 'none') {
        display = 'block';
    } else {
        display = 'none';
    }
    dialog.style.display = display;
}

function closeLoginSignupDialog (evt) {
    document.getElementById("loginsignupdialog").style.display="none";
}

function signupSubmit () {
    var username = document.getElementById('signupemail').value.trim();
    var password = document.getElementById('signuppassword').value.trim();
    var retypepassword = document.getElementById('signupretypepassword').value.trim();
    var question = document.getElementById('signupquestion').value.trim();
    var answer = document.getElementById('signupanswer').value.trim();
    if (username == '' || password == '' || retypepassword == '' || question == '' || answer == '') {
        msgAccountDiv('Fill all the blanks.');
        return;
    }
    if (password != retypepassword) {
        msgAccountDiv('Password mismatch');
        return;
    }
    $.ajax({
        url: '/server/signup',
        data: {'username': username, 'password': password, 'question': question, 'answer': answer},
        success: function (response) {
            if (response == 'already registered') {
                msgAccountDiv('Already registered');
            } else if (response == 'success') {
                /*
                populateJobs();
                msgAccountDiv('Account created');
                document.getElementById('loginsignupbutton').style.display = 'none';
                var userDiv = document.getElementById('userdiv');
                userDiv.textContent = username;
                userDiv.style.display = 'inline-block';
                document.getElementById('logoutdiv').style.display = 'inline-block';
                toggleloginsignupdiv();
                document.getElementById('loginsignupbutton').style.display = 'none';
                document.getElementById('signupdiv').style.display = 'none';
                */
            } else if (response == 'fail') {
                msgAccountDiv('Signup failed');
            }
        }
    });
}

function checkLogged (username) {
    $.ajax({
        url: '/server/checklogged',
        data: {'username': username},
        success: function (response) {
            logged = response['logged'];
            if (logged == true) {
                username = response['email'];
                logged = true;
                doAfterLogin(username);
            } else {
                showUnloggedControl();
            }
        }
    });
}

function showLoggedControl (username) {
    addAccountDiv(username);
    /*
    var userDiv = document.getElementById('userdiv');
    userDiv.textContent = username;
    userDiv.style.display = 'inline-block';
    document.getElementById('logoutdiv').style.display = 'inline-block';
    document.getElementById('headerdiv').style.display = 'block';
    document.getElementById('submitdiv').style.display = 'block';
    */
}

function showUnloggedControl () {
    openLoginPage();
    /*
    var userDiv = document.getElementById('userdiv');
    userDiv.textContent = '';
    userDiv.style.display = 'none';
    document.getElementById('logoutdiv').style.display = 'none';
    document.getElementById('threedotsdiv').style.display = 'none';
    $('#storediv_tabhead[value=storediv]')[0].style.display = 'none';
    document.getElementById('submitdiv').style.display = 'block';
    document.getElementById('storediv').style.display = 'none';
    document.getElementById('loginsignupbutton').style.display = 'none';
    */
}

function doAfterLogin (username) {
    showLoggedControl(username);
    if (username == 'admin') {
        setupAdminMode();
    }
    populateJobs();
}

function setupAdminMode () {
    document.getElementById('settingsdiv').style.display = 'none';
    document.getElementById('threedotsdiv').style.display = 'block';
    $('#storediv_tabhead[value=storediv]')[0].style.display = 'inline-block';
    document.getElementById('submitcontentdiv').style.display = 'none';
}

function msgAccountDiv (msg) {
    document.getElementById('accountmsgdiv').textContent = msg;
    setTimeout(function () {
        document.getElementById('accountmsgdiv').textContent = '';
    }, 3000);
}

function addAccountDiv (username) {
    var div = getEl('div');
    div.id = 'accountdiv';
    var userDiv = getEl('span');
    userDiv.id = 'userdiv';
    userDiv.textContent = username;
    addEl(div, userDiv);
    var logoutDiv = getEl('div');
    addEl(div, logoutDiv);
    var btn = getEl('button');
    btn.addEventListener('click', function (evt) {
        changePassword();
    });
    btn.textContent = 'Change password';
    addEl(logoutDiv, btn);
    var btn = getEl('button');
    btn.addEventListener('click', function (evt) {
        logout();
    });
    btn.textContent = 'Logout';
    addEl(logoutDiv, btn);
    var sdiv = getEl('div');
    sdiv.id = 'changepassworddiv';
    var span = getEl('span');
    span.textContent = 'Old password: ';
    addEl(sdiv, span);
    var input = getEl('input');
    input.type = 'password';
    input.id = 'changepasswordoldpassword';
    addEl(sdiv, input);
    addEl(sdiv, getEl('br'));
    var span = getEl('span');
    span.textContent = 'New password: ';
    addEl(sdiv, span);
    var input = getEl('input');
    input.type = 'password';
    input.id = 'changepasswordnewpassword';
    addEl(sdiv, input);
    addEl(sdiv, getEl('br'));
    var span = getEl('span');
    span.textContent = 'Retype new password: ';
    addEl(sdiv, span);
    var input = getEl('input');
    input.type = 'password';
    input.id = 'changepasswordretypenewpassword';
    addEl(sdiv, input);
    addEl(sdiv, getEl('br'));
    var btn = getEl('button');
    btn.addEventListener('click', function (evt) {
        submitNewPassword();
    });
    btn.textContent = 'Submit';
    addEl(sdiv, btn);
    addEl(div, sdiv);
    var headerDiv = document.getElementById('headerdiv');
    addEl(headerdiv, div);
    /*
    var btn = getEl('button');
    btn.id = 'loginsignupbutton';
    btn.addEventListener('click', function (evt) {
        toggleloginsignupdiv();
    });
    addEl(div, btn);
    */
}

