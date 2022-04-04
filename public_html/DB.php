<?php
/*function sql_connect() 
{
    return 
}*/

function sql_check($userid)
{   
    $connect = mysqli_connect("localhost", "Konstanta", "Reports1234", "zvezda72_Reports");
    
    if ($link == false)
        {
        print("Ошибка: Невозможно подключиться к MySQL " . mysqli_connect_error());
        }
        else 
        {
            print("Соединение установлено успешно");
        }
  /*  $result = mysqli_query($connect, "SELECT id FROM Durka_users WHERE vk_id=$userid");
    return count(mysqli_fetch_array($result));*/
}