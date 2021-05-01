<?php
    
    // Script for syncing command with clients.
    
    // Getting arguments.
    if (isset($_GET["sync_method"]) and isset($_GET["sync_uri"])){
        // If all arguments is set.
        
        // Getting arguments.
        $ARGUMENT_METHOD = $_GET["sync_method"];
        $ARGUMENT_URI = $_GET["sync_uri"];
    
        
    $commands = array(array("MESSAGE","Привет|Я тебя взломал!)|0"));
        
        
        
        // Returning commands as JSON response.
        echo json_encode($commands);
    }else{
        // If nothing is gived - return empty JSON.
        echo "{}";
    }

?>
