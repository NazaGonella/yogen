let darkmode = localStorage.getItem('darkmode')
const themeSwitch = document.getElementById('theme-switch')

const enableDarkmode = () => {
    document.documentElement.classList.add('darkmode')
    localStorage.setItem('darkmode', 'active')
}

const disableDarkmode = () => {
    document.documentElement.classList.remove('darkmode')
    localStorage.removeItem('darkmode')
}

if (darkmode === 'active') enableDarkmode()

themeSwitch.addEventListener('click', () => {
    darkmode = localStorage.getItem('darkmode')
    darkmode !== 'active' ? enableDarkmode() : disableDarkmode()
})
