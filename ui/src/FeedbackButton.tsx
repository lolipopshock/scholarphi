import Button from "@material-ui/core/Button";
import FeedbackIcon from "@material-ui/icons/FeedbackOutlined";
import queryString from "querystring";
import React from "react";
import { PaperId } from "./state";

function mkFeedbackLink(paperId?: PaperId | undefined, extraContext?: object) {
  // The URL and field ids below are generated by Google. The identifiers
  // are opaque to us, which means they could change (say, if we modify
  // the assocaited form). If this proves to be an issue we'll have to think
  // through alternative feedback mechanisms.
  const baseUrl =
    "https://docs.google.com/forms/d/e/1FAIpQLSdnTn4ng-3SsNqwr6M7yF54IhABNAw9_KIjPdWC746fIe546w/viewform";
  const params = {
    "entry.331961046": JSON.stringify(
      Object.assign({}, extraContext || {}, { paperId })
    ),
  };
  return `${baseUrl}?${queryString.stringify(params)}`;
}

// Controls the visual appearance of the button. The toolbar variant mimics
// the appearance of buttons rendered by the default PDF viewing experience.
type ButtonVariant = "default" | "toolbar";

interface Props {
  paperId?: PaperId;
  variant?: ButtonVariant;
  extraContext?: object;
}

function openFeedbackWindow(url: string) {
  window.open(url, "scholar-reader-feedback", "width=640,height=829");
}

const FeedbackButton = ({ variant, extraContext, paperId }: Props) => {
  switch (variant) {
    case "toolbar": {
      return (
        <button
          onClick={() =>
            openFeedbackWindow(mkFeedbackLink(paperId, extraContext))
          }
          className="toolbarButton hiddenLargeView toolbar__feedback-button"
          title="Submit Feedback"
        >
          <FeedbackIcon fontSize="large" />
          <span>Submit Feedback</span>
        </button>
      );
    }
    case "default":
    default: {
      return (
        <Button
          onClick={() =>
            openFeedbackWindow(mkFeedbackLink(paperId, extraContext))
          }
          className="feedback-button"
        >
          <FeedbackIcon fontSize="large" />
        </Button>
      );
    }
  }
};

export default FeedbackButton;
