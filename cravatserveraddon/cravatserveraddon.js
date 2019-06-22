function login () {
    var usernameSubmit = document.getElementById('login_username').value;
    var passwordSubmit = document.getElementById('login_password').value;
    $.ajax({
        url: '/submit/login',
        data: {'username':usernameSubmit, 'password':passwordSubmit},
        success: function (response) {
            if (response == 'success') {
                username = usernameSubmit;
                logged = true;
                doAfterLogin();
            } else if (response == 'fail') {
                msgAccountDiv('Login failed');
            }
        }
    });
}

function logout () {
    $.ajax({
        url: '/submit/logout',
        success: function (response) {
            if (response == 'success') {
                username = '';
                logged = false;
                clearJobTable();
                showUnloggedControl();
            }
        }
    });
}

function getPasswordQuestion () {
    var email = document.getElementById('forgotpasswordemail').value;
    $.ajax({
        url: '/submit/passwordquestion',
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
        url: '/submit/passwordanswer',
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
        url: '/submit/changepassword',
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
        url: '/submit/signup',
        data: {'username': username, 'password': password, 'question': question, 'answer': answer},
        success: function (response) {
            if (response == 'already registered') {
                msgAccountDiv('Already registered');
            } else if (response == 'success') {
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
                document.getElementById('headerdiv').style.display = 'block';
            } else if (response == 'fail') {
                msgAccountDiv('Signup failed');
            }
        }
    });
}

function checkLogged (username) {
    $.ajax({
        url: '/submit/checklogged',
        headers: {'Cache-Control': 'no-cache'},
        data: {'username': username},
        success: function (response) {
            logged = response['logged'];
            if (logged == true) {
                username = response['email'];
                logged = true;
                doAfterLogin();
            } else {
                showUnloggedControl();
            }
        }
    });
}

