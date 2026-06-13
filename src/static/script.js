function toggleAdvancedFilters() {
    const advancedFilters = document.getElementById('advanced_filters');
    const toggleBtn = document.getElementById('toggle_advanced_btn');

    if (advancedFilters.style.display === 'none') {
        // If it's hidden, show it
        advancedFilters.style.display = 'block';
        toggleBtn.innerHTML = '상세조건 닫기 ▲';
    } else {
        // If it's visible, hide it
        advancedFilters.style.display = 'none';
        toggleBtn.innerHTML = '상세조건 열기 ▼';
    }
}

function resetSearchForm() {
    // 1. Clear Text and Date Inputs
    document.getElementById('movie_title_input').value = '';
    document.getElementById('director_input').value = '';

    // 2. Reset Standard Dropdowns (Year From / To)
    document.getElementById('year_from').selectedIndex = 0;
    document.getElementById('year_to').selectedIndex = 0;

    // 3. Uncheck ALL Checkboxes (Movie Type, Genre, Nation)
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    // 4. Reset Custom Dropdown Text back to default
    document.querySelectorAll('.select-box').forEach(box => {
        if (box.parentElement.id === 'genre_custom_select') {
            box.innerHTML = '장르 선택 <span>▼</span>';
        } else if (box.parentElement.id === 'nation_custom_select') {
            box.innerHTML = '국적 선택 <span>▼</span>';
        }
    });

    // 5. Reset Name Indexing Buttons (Hangul/Alphabet)
    document.getElementById('name_index_input').value = '';
    document.querySelectorAll('.idx-btn').forEach(btn => {
        btn.style.backgroundColor = 'white';
        btn.style.color = '#333';
    });

    // 6. Reset the hidden pagination counter to Page 1
    document.getElementById('current_page_input').value = '1';

    // Optional: Auto-submit the empty form to clear the results table completely
    document.getElementById('advanced-search-form').submit(); 

}

function toggleMenu(menuId) {
    const menu = document.getElementById(menuId);
    
    // If it has the 'hidden' class, remove it (show menu). 
    // If it doesn't have it, add it (hide menu).
    menu.classList.toggle('hidden');
}

// 2. Click Outside to Close
// This listens to every click on the whole webpage. 
// If you click outside a menu, it automatically closes it.
document.addEventListener('click', function(event) {
    const customSelects = document.querySelectorAll('.custom-select');
    
    customSelects.forEach(select => {
        // Check if the click happened OUTSIDE this specific dropdown
        if (!select.contains(event.target)) {
            const menu = select.querySelector('.checkbox-menu');
            if (!menu.classList.contains('hidden')) {
                menu.classList.add('hidden');
            }
        }
    });
});

// 3. Dynamic Text Updating
// This changes the text of the box to show what you selected
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.checkbox-menu').forEach(menu => {
        const checkboxes = menu.querySelectorAll('input[type="checkbox"]');
        const selectBox = menu.previousElementSibling; 
        
        // Save the original text (e.g., "장르 선택 ▼")
        const originalText = selectBox.innerHTML;

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                // Find all checkboxes inside this specific menu that are checked
                const checked = Array.from(checkboxes).filter(cb => cb.checked);
                
                if (checked.length === 0) {
                    selectBox.innerHTML = originalText;
                } else if (checked.length === 1) {
                    // Show "액션 ▼"
                    selectBox.innerHTML = checked[0].value + ' <span>▼</span>';
                } else {
                    // Show "액션 외 1건 ▼"
                    selectBox.innerHTML = checked[0].value + ' 외 ' + (checked.length - 1) + '건 <span>▼</span>';
                }
            });
        });
    });
});

// 4. Movie Name Indexing (Alphabet/Hangul Buttons)
// This runs when you click 'ㄱ' or 'A'
function setIndex(letter) {
    // 1. Save the letter in the hidden input so Python can read it
    document.getElementById('name_index_input').value = letter;
    
    // 2. Reset the colors of all index buttons back to white
    document.querySelectorAll('.idx-btn').forEach(btn => {
        btn.style.backgroundColor = 'white';
        btn.style.color = '#333';
    });
    
    // 3. Highlight the specific button you just clicked in blue
    event.target.style.backgroundColor = '#1a237e';
    event.target.style.color = 'white';
}

// --- PAGINATION SCRIPT ---

// 1. When a pagination button is clicked
function changePage(pageNumber) {
    // Set the hidden input to the new page number
    document.getElementById('current_page_input').value = pageNumber;
    // Resubmit the form with all the existing filters
    document.getElementById('advanced-search-form').submit();
}

// 2. When the main Search button is clicked
function resetPage() {
    // Always reset back to page 1 when doing a brand new search
    document.getElementById('current_page_input').value = 1;
}

function openMovieDetails(mid) {
    fetch(`/movie/${mid}`)
        .then(response => response.json())
        .then(data => {
            if(data.error) return;

            // 제목 설정
            let title = data['영화명'];
            if (data['영문명']) title += ` <span style="font-size:0.8em; color:#666;">(${data['영문명']})</span>`;
            document.getElementById('modal_title').innerHTML = title;
            
            // 데이터 삽입
            document.getElementById('modal_code').innerText = data['Mid'];
            
            // 요약정보 조합 (유형 | 장르 | 국가)
            let summaryArray = [];
            if(data['유형']) summaryArray.push(data['유형']);
            if(data['장르']) summaryArray.push(data['장르']);
            if(data['국적']) summaryArray.push(data['국적']);
            document.getElementById('modal_summary').innerText = summaryArray.length > 0 ? summaryArray.join(' | ') : '해당정보 없음';
            
            document.getElementById('modal_year').innerText = data['제작연도'] ? data['제작연도'] + '년' : '해당정보 없음';
            document.getElementById('modal_status').innerText = data['제작상태'] || '해당정보 없음';
            
            // 나머지 필드는 데이터가 없으므로 기본값(해당정보 없음) 유지
            // (나중에 DB에 추가되면 여기에서 data['필드명']으로 연결하세요)

            document.getElementById('movieModal').style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
}

function closeModal() {
    document.getElementById('movieModal').style.display = 'none';
}