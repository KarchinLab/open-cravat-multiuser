function openSubmitPage (username) {
    location.href = location.protocol + '//' + window.location.host + '/submit/index.html?username=' + username;
}

function openLoginPage () {
    location.href = location.protocol + '//' + window.location.host + '/server/nocache/login.html';
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
    document.querySelector('.threedotsdiv').style.display = 'block';
    $('#storediv_tabhead[value=storediv]')[0].style.display = 'inline-block';
    $('#admindiv_tabhead[value=admindiv]')[0].style.display = 'inline-block';
    document.getElementById('admindiv_tabhead').setAttribute('disabled', 'f');
    document.getElementById('submitcontentdiv').style.display = 'none';
    populateAdminTab();
}

function getDateStr (d) {
    var year = d.getFullYear();
    var month = d.getMonth() + 1;
    if (month < 10) {
        month = '0' + month;
    } else {
        month = '' + month;
    }
    var day = d.getDate();
    if (day < 10) {
        day = '0' + day;
    } else {
        day = '' + day;
    }
    var datestr = year + '-' + month + '-' + day;
    return datestr;
}

function populateAdminTab () {
    var div = document.getElementById('admindiv');
    // date range
    var sdiv = getEl('div');
    var span = getEl('span');
    span.textContent = 'Date range:';
    addEl(sdiv, span);
    var input = getEl('input');
    input.id = 'admindiv-startdate-input';
    input.type = 'date';
    input.style.marginLeft = '10px';
    var startDate = new Date();
    var startDate = new Date(startDate.setDate(startDate.getDate() - 7));
    var datestr = getDateStr(startDate);
    input.value = datestr;
    addEl(sdiv, input);
    var span = getEl('span');
    span.textContent = '~';
    span.style.marginLeft = '10px';
    addEl(sdiv, span);
    var input = getEl('input');
    input.id = 'admindiv-enddate-input';
    input.type = 'date';
    input.style.marginLeft = '10px';
    var datestr = getDateStr(new Date());
    input.value = datestr;
    addEl(sdiv, input);
    var btn = getEl('button');
    btn.textContent = 'Update';
    btn.style.marginLeft = '10px';
    btn.addEventListener('click', function (evt) {
        updateAdminTabContent();
    });
    addEl(sdiv, btn);
    addEl(div, sdiv);
    // input stat
    var sdiv = getEl('div');
    sdiv.id = 'admindiv-inputstat-div';
    sdiv.className = 'adminsection-div';
    addEl(div, sdiv);
    var span = getEl('span');
    span.className = 'adminsection-title';
    span.textContent = 'Input Stats';
    addEl(sdiv, span);
    var ssdiv = getEl('div');
    ssdiv.id = 'admindiv-inputstat-contentdiv';
    addEl(sdiv, ssdiv);
    // job stat
    var sdiv = getEl('div');
    sdiv.id = 'admindiv-jobstat-div';
    sdiv.className = 'adminsection-div';
    addEl(div, sdiv);
    var span = getEl('span');
    span.className = 'adminsection-title';
    span.textContent = 'Job Stats';
    addEl(sdiv, span);
    var ssdiv = getEl('div');
    ssdiv.id = 'admindiv-jobstat-contentdiv';
    addEl(sdiv, ssdiv);
    // user stat
    var sdiv = getEl('div');
    sdiv.id = 'admindiv-userstat-div';
    sdiv.className = 'adminsection-div';
    addEl(div, sdiv);
    var span = getEl('span');
    span.className = 'adminsection-title';
    span.textContent = 'User Stats';
    addEl(sdiv, span);
    var ssdiv = getEl('div');
    ssdiv.id = 'admindiv-userstat-contentdiv';
    addEl(sdiv, ssdiv);
    // annotation stat
    var sdiv = getEl('div');
    sdiv.id = 'admindiv-annotstat-div';
    sdiv.className = 'adminsection-div';
    addEl(div, sdiv);
    var span = getEl('span');
    span.className = 'adminsection-title';
    span.textContent = 'Annotation Stats';
    addEl(sdiv, span);
    var ssdiv = getEl('div');
    ssdiv.id = 'admindiv-annotstat-contentdiv';
    addEl(sdiv, ssdiv);
    // assembly stat
    var sdiv = getEl('div');
    sdiv.id = 'admindiv-assemblystat-div';
    sdiv.className = 'adminsection-div';
    addEl(div, sdiv);
    var span = getEl('span');
    span.className = 'adminsection-title';
    span.textContent = 'Assembly Stats';
    addEl(sdiv, span);
    var ssdiv = getEl('div');
    ssdiv.id = 'admindiv-assemblystat-contentdiv';
    addEl(sdiv, ssdiv);
    updateAdminTabContent();
}

function updateAdminTabContent () {
    populateInputStatDiv();
    populateUserStatDiv();
    populateJobStatDiv();
    populateAnnotStatDiv();
    populateAssemblyStatDiv();
}

function populateInputStatDiv () {
    var startDate = document.getElementById('admindiv-startdate-input').value;
    var endDate = document.getElementById('admindiv-enddate-input').value;
    var sdiv = document.getElementById('admindiv-inputstat-contentdiv');
    $(sdiv).empty();
    var table = getEl('table');
    addEl(sdiv, table);
    $.ajax({
        url: '/server/inputstat',
        data: {'start_date':startDate, 'end_date':endDate},
        success: function (response) {
            var totN = response[0];
            var maxN = response[1];
            var avgN = response[2];
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Total number of input lines:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = totN;
            addEl(tr, td);
            addEl(table, tr);
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Maximum number of input lines:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = maxN;
            addEl(tr, td);
            addEl(table, tr);
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Average number of input lines:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = Math.round(avgN);
            addEl(tr, td);
            addEl(table, tr);
        },
    });
}

function populateUserStatDiv () {
    var startDate = document.getElementById('admindiv-startdate-input').value;
    var endDate = document.getElementById('admindiv-enddate-input').value;
    var sdiv = document.getElementById('admindiv-userstat-contentdiv');
    $(sdiv).empty();
    var table = getEl('table');
    addEl(sdiv, table);
    $.ajax({
        url: '/server/userstat',
        data: {'start_date':startDate, 'end_date':endDate},
        success: function (response) {
            //
            var num_uniq_user = response['num_uniq_user'];
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Number of unique users:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = num_uniq_user;
            addEl(tr, td);
            addEl(table, tr);
            //
            var frequent = response['frequent'];
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Most frequent user:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = frequent[0];
            addEl(tr, td);
            addEl(table, tr);
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = '\xa0\xa0Number of jobs:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = frequent[1];
            addEl(tr, td);
            addEl(table, tr);
            //
            var heaviest = response['heaviest'];
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Heaviest user:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = heaviest[0];
            addEl(tr, td);
            addEl(table, tr);
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = '\xa0\xa0Number of input:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = heaviest[1];
            addEl(tr, td);
            addEl(table, tr);
        },
    });
}

function populateJobStatDiv () {
    var startDate = document.getElementById('admindiv-startdate-input').value;
    var endDate = document.getElementById('admindiv-enddate-input').value;
    var sdiv = document.getElementById('admindiv-jobstat-contentdiv');
    $(sdiv).empty();
    var table = getEl('table');
    addEl(sdiv, table);
    var canvas = getEl('canvas');
    addEl(sdiv, canvas);
    $.ajax({
        url: '/server/jobstat',
        data: {'start_date':startDate, 'end_date':endDate},
        success: function (response) {
            //
            var num_jobs = response['num_jobs'];
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Total number of jobs:\xa0';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = num_jobs;
            addEl(tr, td);
            addEl(table, tr);
            var chartdata = response['chartdata'];
            var submits = chartdata[0];
            var counts = chartdata[1];
			var chart = new Chart(canvas, {
				type: 'bar',
				data: {
					datasets: [{
						data: counts,
					}],
					labels: submits,
				},
                options: {
                    scales: {
                        xAxes: [{
                            type: 'time',
                            time: {
                                unit: 'day',
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Date',
                            },
                        }],
                        yAxes: [{
                            ticks: {
                                min: 0,
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Number of Jobs',
                            },
                        }],
                    },
                    elements: {
                        line: {
                            tension: 0,
                        },
                    },
                    legend: {
                        display: false,
                    },
                },
			});
        },
    });
}

function populateAnnotStatDiv () {
    var startDate = document.getElementById('admindiv-startdate-input').value;
    var endDate = document.getElementById('admindiv-enddate-input').value;
    var sdiv = document.getElementById('admindiv-annotstat-contentdiv');
    $(sdiv).empty();
    sdiv.style.width = '800px';
    sdiv.style.height = '700px';
    var table = getEl('table');
    addEl(sdiv, table);
    var chartdiv = getEl('canvas');
    chartdiv.id = 'admindiv-annotstat-chart1';
    /*
    chartdiv.style.width = '400px';
    chartdiv.style.height = '400px';
    chartdiv.width = 400;
    chartdiv.height = 400;
    */
    addEl(sdiv, chartdiv);
    $.ajax({
        url: '/server/annotstat',
        data: {'start_date':startDate, 'end_date':endDate},
        success: function (response) {
            //
            var annotCount = response['annot_count'];
            var annots = Object.keys(annotCount);
            for (var i = 0; i < annots.length - 1; i++) {
                for (var j = i + 1; j < annots.length; j++) {
                    if (annotCount[annots[i]] < annotCount[annots[j]]) {
                        var tmp = annots[i];
                        annots[i] = annots[j];
                        annots[j] = tmp;
                    }
                }
            }
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Module';
            td.style.textDecoration = 'underline';
            td.style.textDecorationColor = '#aaaaaa';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = 'Number of jobs';
            td.style.textDecoration = 'underline';
            td.style.textDecorationColor = '#aaaaaa';
            addEl(tr, td);
            addEl(table, tr);
            var tbody = getEl('tbody');
            addEl(table, tbody);
            var counts = [];
            for (var i = 0; i < annots.length; i++) {
                var tr = getEl('tr');
                var td = getEl('td');
                td.textContent = annots[i];
                addEl(tr, td);
                var td = getEl('td');
                td.textContent = annotCount[annots[i]];
                counts.push(annotCount[annots[i]]);
                addEl(tr, td);
                addEl(table, tr);
            }
			var chart = new Chart(chartdiv, {
				type: 'doughnut',
				data: {
					datasets: [{
						data: counts,
					}],
					labels: annots,
				},
			});
        },
    });
}

function populateAssemblyStatDiv () {
    var startDate = document.getElementById('admindiv-startdate-input').value;
    var endDate = document.getElementById('admindiv-enddate-input').value;
    var sdiv = document.getElementById('admindiv-assemblystat-contentdiv');
    $(sdiv).empty();
    var table = getEl('table');
    addEl(sdiv, table);
    $.ajax({
        url: '/server/assemblystat',
        data: {'start_date':startDate, 'end_date':endDate},
        success: function (response) {
            var thead = getEl('thead');
            var tr = getEl('tr');
            var td = getEl('td');
            td.textContent = 'Genome assembly';
            td.style.textDecoration = 'underline';
            td.style.textDecorationColor = '#aaaaaa';
            addEl(tr, td);
            var td = getEl('td');
            td.textContent = 'Number of jobs';
            td.style.textDecoration = 'underline';
            td.style.textDecorationColor = '#aaaaaa';
            addEl(tr, td);
            addEl(table, tr);
            var tbody = getEl('tbody');
            addEl(table, tbody);
            for (var i = 0; i < response.length; i++) {
                var tr = getEl('tr');
                var td = getEl('td');
                td.textContent = response[i][0];
                addEl(tr, td);
                var td = getEl('td');
                td.textContent = response[i][1];
                addEl(tr, td);
                addEl(table, tr);
            }
        },
    });
}

/*
function getEl (tag) {
    return document.createElement(tag);
}

function addEl (pelem, child) {
	pelem.appendChild(child);
	return pelem;
}

function showYesNoDialog (content, yescallback, noSpace, justOk) {
    var div = document.getElementById('yesnodialog');
    if (div != undefined) {
        $(div).remove();
    }
    var div = getEl('div');
    div.id = 'yesnodialog';
    content.id = 'yesnodialog-contentdiv'
    addEl(div, content);
    addEl(div, getEl('br'));
    var btnDiv = getEl('div');
    if (justOk) {
        btnDiv.className = 'buttondiv';
        var btn = getEl('button');
        btn.textContent = 'Ok';
        btn.addEventListener('click', function (evt) {
            $('#yesnodialog').remove();
        });
        addEl(btnDiv, btn);
    } else {
        btnDiv.className = 'buttondiv';
        var btn = getEl('button');
        btn.textContent = 'Yes';
        btn.addEventListener('click', function (evt) {
            $('#yesnodialog').remove();
            yescallback(true);
        });
        if (noSpace) {
            btn.disabled = true;
            btn.style.backgroundColor = '#e0e0e0';
        }
        addEl(btnDiv, btn);
        var btn = getEl('button');
        btn.textContent = 'No';
        btn.addEventListener('click', function (evt) {
            $('#yesnodialog').remove();
            yescallback(false);
        });
        addEl(btnDiv, btn);
    }
    addEl(div, btnDiv);
    addEl(document.body, div);
}
*/

function msgAccountDiv (msg) {
    var div = getEl('div');
    div.textContent = msg;
    showYesNoDialog(div, null, false, true);
    //function showYesNoDialog (content, yescallback, noSpace, justOk) {
}

function addAccountDiv (username) {
    var div = getEl('div');
    div.id = 'accountdiv';
    var userDiv = getEl('span');
    userDiv.id = 'userdiv';
    userDiv.textContent = username + '\xa0';
    addEl(div, userDiv);
    var logoutDiv = getEl('div');
    logoutDiv.id = 'logdiv';
    addEl(div, logoutDiv);
    var btn = getEl('img');
    btn.src = '/server/pwchng.png';
    btn.addEventListener('click', function (evt) {
        changePassword();
    });
    btn.title = 'Change password';
    addEl(logoutDiv, btn);
    var span = getEl('span');
    span.textContent = '\xa0\xa0';
    addEl(logoutDiv, span);
    var btn = getEl('img');
    btn.src = '/server/logout.png';
    btn.addEventListener('click', function (evt) {
        logout();
    });
    btn.title = 'Logout';
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
    btn.classList.add('butn');
    btn.addEventListener('click', function (evt) {
        submitNewPassword();
    });
    btn.textContent = 'Submit';
    addEl(sdiv, btn);
    addEl(div, sdiv);
    var headerDiv = document.querySelector('.headerdiv');
    addEl(headerDiv, div);
    /*
    var btn = getEl('button');
    btn.id = 'loginsignupbutton';
    btn.addEventListener('click', function (evt) {
        toggleloginsignupdiv();
    });
    addEl(div, btn);
    */
}

