const modal = document.querySelector('.modal');
const menuSearchModal=document.querySelector(".menuSearch"); // querySelector('.btn-open-modal');
const whatMenuInput = document.getElementById("whatMenu"); // 모달창 검색할 메뉴 input태그 id

// 메뉴 검색 아이콘 클릭하면 모달창 띄우기
menuSearchModal.addEventListener("click", ()=>{
    // 로그인 여부 확인하고 모달창 열어주기
    fetch("/get_user").then(res => res.json()).then(data => {
      if (data.user) { // true값이 들어오면 로그인 성공
        modal.style.display = "flex";
      } else {
        alert("로그인이 필요합니다.");
      }
    });

    //modal.style.display="flex";
});

// 모달창 닫기
const closeBtn = document.querySelector(".close");
closeBtn.addEventListener("click", () => {
  modal.style.display = "none";
  // 입력 필드 초기화
  if (whatMenuInput) {
    whatMenuInput.value = "";
  }

});

// 메뉴 검색 DB연결부분 => post를 쓸 때 토큰을 함께 넘겨줘야 route에 도달함. 
function goToSearchMenu(){
  const searchMenu = document.getElementById("whatMenu").value;
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
 
  $.ajax({
    url : "/menuSearch",
    type : "post",
    data : {
      searchMenu : searchMenu, 
      csrf_token : csrfToken
    },
    dataType : "json",
    success: function(response) { //json 형태의 response 응답 데이터받기
      
      // 검색된 데이터를 들고 검색된 매출 조회 화면으로 이동
      const form = document.createElement("form");
      form.method = "POST";
      form.action = "/viewSearchMenu";
      const inputData = document.createElement("input");
      inputData.type = "hidden";
      inputData.name = "searchData"; // 서버에서 받을 때 사용할 이름
      inputData.value = response; // 메뉴 검색 결과 데이터 (서버에서 받은 JSON 데이터 전달)
      form.appendChild(inputData); // form에 inputData 추가
      

      // CSRF 토큰 추가
      const inputToken = document.createElement("input");
      inputToken.type = "hidden";
      inputToken.name = "csrf_token"; // Flask-WTF가 요구하는 이름
      inputToken.value = csrfToken;   // 위에서 받은 토큰
      form.appendChild(inputToken); // form에 inputToken 추가

      document.body.appendChild(form); // 이동할 페이지에 form 추가
      form.submit(); // 페이지 이동 + 데이터 전송

    },
    error: function(xhr, status, error) {
      console.error("에러 발생:", error);
    }
  })
}