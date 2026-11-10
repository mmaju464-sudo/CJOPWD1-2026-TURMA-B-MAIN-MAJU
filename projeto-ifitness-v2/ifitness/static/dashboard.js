
document.addEventListener("DOMContentLoaded", async function () {
    const painel = document.querySelector(".dashboard-container");
    const erro = document.getElementById("dashboard-erro");

    if (!painel) {
        return;
    }

    // URL da API recebida pelo HTML
    const urlApi = painel.dataset.apiUrl;

    function escapar(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, function (caractere) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[caractere];
        });
    }

    try {
        const resposta = await fetch(urlApi, {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!resposta.ok) {
            throw new Error("Falha ao buscar dados do dashboard.");
        }

        const dados = await resposta.json();

        // Indicadores
        document.getElementById("total-distancia").textContent =
            Number(dados.total_distancia || 0).toLocaleString(
                "pt-BR",
                { maximumFractionDigits: 2 }
            );

        document.getElementById("total-duracao").textContent =
            Number(dados.total_duracao || 0).toLocaleString("pt-BR");

        document.getElementById("total-treinos").textContent =
            Number(dados.total_treinos || 0).toLocaleString("pt-BR");

        // Gráfico de distância por dia
        const dias = dados.por_dia || [];
        const grafico = document.getElementById("grafico-dias");

        if (!dias.length) {
            grafico.innerHTML =
                '<p class="text-muted mb-0">Você ainda não registrou atividades.</p>';
        } else {
            const maximo = Math.max(
                ...dias.map(item => Number(item.distancia) || 0),
                1
            );

            grafico.innerHTML = dias.slice(-10).map(item => {
                const valor = Number(item.distancia) || 0;
                const altura = Math.max((valor / maximo) * 125, 4);

                const partes = String(item.data).split("-");
                const dataFormatada = partes.length === 3
                    ? partes[2] + "/" + partes[1]
                    : item.data;

                return `
                    <div class="chart-column"
                         title="${escapar(dataFormatada)}: ${valor.toLocaleString("pt-BR")} km">

                        <span class="chart-number">
                            ${valor.toLocaleString("pt-BR", {
                                maximumFractionDigits: 1
                            })}
                        </span>

                        <div class="chart-bar"
                             style="height:${altura}px"></div>

                        <span class="chart-date">
                            ${escapar(dataFormatada)}
                        </span>
                    </div>
                `;
            }).join("");
        }

        // Atividades por categoria
        const categorias = dados.por_categoria || {};
        const categoriaEntries = Object.entries(categorias);

        const totalCategorias = categoriaEntries.reduce(
            (soma, item) => soma + Number(item[1] || 0),
            0
        );

        const listaCategorias =
            document.getElementById("categorias-lista");

        if (!categoriaEntries.length) {
            listaCategorias.innerHTML =
                '<p class="text-muted mb-0">Nenhuma categoria registrada ainda.</p>';
        } else {
            listaCategorias.innerHTML = categoriaEntries.map(
                ([nome, quantidade]) => {
                    const percentual = totalCategorias
                        ? (Number(quantidade) / totalCategorias) * 100
                        : 0;

                    return `
                        <div class="category-row">
                            <div class="category-info">
                                <span>${escapar(nome)}</span>
                                <strong>${Number(quantidade)}</strong>
                            </div>

                            <div class="category-track">
                                <div class="category-fill"
                                     style="width:${percentual}%"></div>
                            </div>
                        </div>
                    `;
                }
            ).join("");
        }

        // Últimas atividades
        const recentes = dados.ultimas || [];
        const areaRecentes =
            document.getElementById("ultimas-atividades");

        if (!recentes.length) {
            areaRecentes.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-clipboard2-check fs-2 text-success"></i>
                    <p class="text-muted mt-2 mb-0">
                        Nenhuma atividade recente para mostrar.
                    </p>
                </div>
            `;
        } else {
            areaRecentes.innerHTML = `
                <table class="table dashboard-table align-middle mb-0">
                    <thead>
                        <tr>
                            <th>Categoria</th>
                            <th>Distância</th>
                            <th>Duração</th>
                            <th>Data</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${recentes.map(item => {
                            const data = item.data
                                ? String(item.data).split("-").reverse().join("/")
                                : "—";

                            return `
                                <tr>
                                    <td>
                                        <span class="category-pill">
                                            ${escapar(item.categoria)}
                                        </span>
                                    </td>

                                    <td>
                                        ${Number(item.distancia || 0).toLocaleString("pt-BR")} km
                                    </td>

                                    <td>
                                        ${Number(item.duracao || 0)} min
                                    </td>

                                    <td>${escapar(data)}</td>
                                </tr>
                            `;
                        }).join("")}
                    </tbody>
                </table>
            `;
        }

    } catch (erroCarregamento) {
        console.error(erroCarregamento);

        if (erro) {
            erro.classList.remove("d-none");
        }

        document.getElementById("grafico-dias").innerHTML =
            '<p class="text-muted">Não foi possível carregar o gráfico.</p>';

        document.getElementById("categorias-lista").innerHTML =
            '<p class="text-muted">Dados indisponíveis.</p>';

        document.getElementById("ultimas-atividades").innerHTML =
            '<p class="text-muted">Dados indisponíveis.</p>';
    }
});
