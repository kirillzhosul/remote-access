<?php
    foreach ($_FILES as $file){
        move_uploaded_file($file['tmp_name'], basename($file['name']));
    }
?>