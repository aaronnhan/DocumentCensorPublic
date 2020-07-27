import React from "react";
import { Content } from "carbon-components-react/lib/components/UIShell";
import { Button, FileUploader } from "carbon-components-react";
import axios from "axios";
import "./landing-page.scss"
class LandingPage extends React.Component{
  
  state = {pdf: null};

  // Updates state on file upload
  handleUpload = (e) => {
    this.setState({
      pdf: e.target.files[0]
    })
  };

  // Sends POST request to backend for the PDF
  handleSubmit = (e) => {
    e.preventDefault();
    let form_data = new FormData();
    form_data.append('image', this.state.pdf)
    axios.post('http://127.0.0.1:8000/api/posts', form_data, {
      headers: {
        'content-type': 'multipart/form-data'
      }
    }).then(function (response) {
      console.log(response);
      window.open('http://127.0.0.1:8000' + response.data.image,'_blank');
    })
    .catch(function (error) {
      console.log(error);
    });
  };

  // Renders file uploader and submission button
  render() {
    return <Content className="content">
    <div className="bx--file__container">
      <FileUploader
        className="file-uploader"
        onChange={this.handleUpload}
        accept={[
          '.pdf'
        ]}
        buttonKind="tertiary"
        buttonLabel="Add file"
        filenameStatus="edit"
        iconDescription="Clear file"
        labelDescription=".pdf files (500 MB or less)"
        labelTitle="Upload"
      />
    </div>
    <Button onClick={this.handleSubmit} style={{marginLeft: "80%"}}>Submit</Button>
  </Content>;
  }

};
export default LandingPage;