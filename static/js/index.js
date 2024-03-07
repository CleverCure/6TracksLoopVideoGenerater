file_check = 0;
// console.log(file_check);

$('#file_check').change(function() {
    file_check = $("#file_check").val().length;
    // console.log(file_check);
});

$('#submit_button').on('click', function() {
    if (file_check !== 0) {
        $('.form_area').css('display', 'none');
        $('.loading_area').fadeIn();
    }
});
