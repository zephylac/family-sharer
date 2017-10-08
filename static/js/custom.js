$(document).ready (function(){
  $(".alert").fadeTo(2000, 500).slideUp(500, function(){
  $(".alert").slideUp(500);
  });
});

// Get the modal
var modal = document.getElementById('ModalImg');
var modalImg = document.getElementById("img-content");
var captionText = document.getElementById("img-caption");
var span = document.getElementById("img-close");
console.log(span);
span.onclick = function() { 
  modal.style.display = "none";
}

// on click on each image show in the above modal
var imgs = document.getElementsByClassName("img-modal");
for (let i = 0; i < imgs.length; i++) {
  imgs[i].onclick = function(){
    modal.style.display = "block";
    modalImg.src = this.src;
    captionText.innerHTML = this.alt;
  }
}
