import { useState } from "react";
import {Navbar, Container} from "react-bootstrap";
{/* Mentioned in video but I do not wish to download pngs from an unknown github*/}
{/*import navIcon1 from '../assets/img/nav-icon1.svg */}
{/*import navIcon2 from '../assets/img/nav-icon2.svg */}
{/*import navIcon3 from '../assets/img/nav-icon3.svg */}

export const NavBar = () => {
    const [activeLink, setActiveLink] = useState('home');
    const [scrolled, seScrolled] = useState(false);

    useEffect(() => {
      const onScroll = () => {
        if (window.scrollY > 50) {
          seScrolled(true);
        } else {
          seScrolled(false);
        }
      }

      window.addEventListener("scroll", onScroll);

      return () => window.removeEventListener("scroll", onScroll);
    }, [])

    return(
        <Navbar bg="light" expand="lg" className={scrolled ? "scrolled": ""}>
        <Container>
        {/* Name for Navbar, can have name after href="#home">(insert name here) or put an img. Going to put image to follow tutorial for now. */}
          <Navbar.Brand href="#home">
            {/*Uses logo from import. Code will not run until I get my own logos */}
            <img src={logo} alt="Logo"/>
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" >
            <span className="navbar-toggler-icon"></span>
          </Navbar.Toggle>
          <Navbar.Collapse id="basic-navbar-nav" >
            <Nav className="me-auto">
              <Nav.Link href="#home" className={acitveLink === 'home' ? 'active navbar-link' : 'navbar-link'} onClick={() => onUpdateActiveLink('home')} >Home</Nav.Link>
              <Nav.Link href="#skills" className={activeLink === 'skills' ? 'active navbar-link' : 'navbar-link'} onClick={() => onUpdateActiveLink('skills')}>Skills</Nav.Link>
              <Nav.Link href='#projects' className={activeLink === 'projects' ? 'active navbar-link' : 'navbar-link'} onClick={() => onUpdateActiveLink('home')}>Projects</Nav.Link>
            </Nav>
            <span className="navbar-text">
              <div className="social-icon">
                {/**Navicon not imported yet */}
                <a href="#"><img src={navIcon1} alt="" /></a>
                <a href="#"><img src={navIcon2} alt="" /></a>
                <a href="#"><img src={navIcon3} alt="" /></a>
              </div>
              <button className="vvd" onClick={() => console.log('connect')}><span>Let's Connect</span></button>
            </span>
          </Navbar.Collapse>
        </Container>
      </Navbar>
    )
}