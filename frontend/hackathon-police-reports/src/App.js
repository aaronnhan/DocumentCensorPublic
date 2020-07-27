import React from 'react';
import "./app.scss";
import { Button } from "carbon-components-react";
import { Content } from "carbon-components-react/lib/components/UIShell";
import HackathonHeader from "./components/HackathonHeader";
import { Route, Switch } from "react-router-dom";
import LandingPage from "./content/LandingPage";
import AppPage from "./content/AppPage";

class App extends React.Component {

  // Renders header and page components
  render() {
    return (
      <>
        <HackathonHeader />
        <Switch>
          <Route exact path="/" component={LandingPage} />
          <Route path="/repos" component={AppPage} />
        </Switch>
      </>
    );
  }

}

export default App;