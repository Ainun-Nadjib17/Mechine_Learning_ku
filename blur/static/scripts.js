const clock = document.getElementById("clock");

function updateClock() {

    const now = new Date();

    clock.innerHTML = now.toLocaleTimeString();

}

setInterval(updateClock, 1000);

updateClock();



const video = document.getElementById("camera");
const canvas = document.getElementById("output");

const ctx = canvas.getContext("2d");


const statusText = document.getElementById("status");
const aiStatus = document.getElementById("aiStatus");

const dot = document.querySelector(".dot");



canvas.width = 640;
canvas.height = 480;



// Aktifkan kamera user
navigator.mediaDevices.getUserMedia({

    video: {
        width: 640,
        height: 480
    }

})
.then(stream => {


    video.srcObject = stream;


    statusText.innerHTML = "Camera Connected";

    dot.style.background = "limegreen";



    video.onloadedmetadata = () => {


        aiStatus.innerHTML = "Running";


        requestAnimationFrame(sendFrame);


    };


})
.catch(err => {


    console.error(err);


    statusText.innerHTML = "Camera Disconnected";

    aiStatus.innerHTML = "Stopped";

    dot.style.background = "red";


});



let processing = false;



async function sendFrame() {


    if (!processing) {


        processing = true;



        try {


            // ambil frame kamera

            ctx.drawImage(
                video,
                0,
                0,
                640,
                480
            );



            const image = canvas.toDataURL(
                "image/jpeg",
                0.7
            );



            const response = await fetch("/detect", {


                method: "POST",


                headers: {

                    "Content-Type": "application/json"

                },


                body: JSON.stringify({

                    image:image

                })


            });



            const data = await response.json();



            if(data.image){


                const img = new Image();



                img.onload = () => {


                    ctx.drawImage(
                        img,
                        0,
                        0,
                        640,
                        480
                    );


                };



                img.src =
                "data:image/jpeg;base64," + data.image;



            }



            aiStatus.innerHTML =
                data.blur
                ? "Peace Detected"
                : "Running";



        }

        catch(err){


            console.error(err);


            aiStatus.innerHTML =
            "Server Offline";


        }



        processing = false;


    }



    requestAnimationFrame(sendFrame);


}