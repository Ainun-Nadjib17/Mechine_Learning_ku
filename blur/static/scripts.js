const clock = document.getElementById("clock");

function updateClock(){

    const now = new Date();

    clock.innerHTML = now.toLocaleTimeString();

}

setInterval(updateClock,1000);

updateClock();

const video=document.getElementById("video");

video.onload=()=>{

    document.getElementById("aiStatus").innerHTML="Running";

}

video.onerror=()=>{

    document.getElementById("status").innerHTML="Disconnected";

    document.querySelector(".dot").style.background="red";

}