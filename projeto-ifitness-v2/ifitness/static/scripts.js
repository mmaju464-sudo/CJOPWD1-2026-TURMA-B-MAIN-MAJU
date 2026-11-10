const myModal = document.getElementById('myModal');

if (myModal) {
    myModal.addEventListener('show.bs.modal', event => {
        const button = event.relatedTarget;
        const idAtividade = button.getAttribute('data-atividade-id');
        const confirmBtn = myModal.querySelector('#delete');

        if (confirmBtn) {
            confirmBtn.href = "/excluir_atividade/" + idAtividade;
        }
    });
}