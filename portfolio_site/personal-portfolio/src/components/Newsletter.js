import {Alert} from "react-bootstrap";
import {useState} from "react";

export const Newsletter = ({subscribe, status, message}) => {
    const [email, setEmail] = useState('');

    useEffect(() => {
        if(status === 'success') clearFields();
        }, [status])
    const handleSubmit = () => {
        e.preventDefault();
        email &&
        email.index0f("@") > -1 &&
        onValidated({
            EMAIL: email
        })
    }
    
    return (
        <Col lg={12}>
            <div className="newsletter-bx">
                <Row>
                    <Col lg={12} md={6} xl={5}>
                    <h3> Subscribe to my Newsletter</h3>
                    {status === 'sending' && <Alert>Sending...</Alert>}
                    {status === 'error' && <Alert variant="danger">Sending...</Alert>}
                    {status === 'sending' && <Alert>Sending...</Alert>}
                    </Col>
                    <Col md={6} xl={7}>
                    <form onSubmit={handleSubmit}>
                        <div className="new-email-bx">
                            <input value={email} type="email" onChange={(e) => setEmail(e.target.value)} />
                        </div>
                    </form>
                    </Col>
                </Row>
            </div>
        </Col>
    )
}