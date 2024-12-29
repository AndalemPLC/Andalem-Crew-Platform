class CustomStyles:

    custom_style = """
                        <style>

                            footer {visibility: hidden;}
                            header {visibility: visible;}
                            #MainMenu {visibility: visible;}

                            [data-testid=ScrollToBottomContainer] {
                                margin-top: -3rem;
                            }

                            [data-testid=stSidebarUserContent] {
                                margin-top: -3rem;
                            }
                            
                            [data-testid=stImage] {                                
                                text-align: center;
                                display: block;
                                margin-left: auto;
                                margin-right: auto;
                                width: 100%;
                            }

                            .app-logo img {                                
                                width: 10vw;
                            }

                            [data-testid=stImageCaption] {
                                text-align: center;
                                display: block;
                                margin-left: auto;
                                margin-right: auto;
                                width: 100%;
                            }

                            .app-name {                             
                                font-weight: bold;
                                text-align: center;
                                display: block;
                                margin-left: auto;
                                margin-right: auto;
                                width: 100%;
                            }

                            .number-of-agents {
                                text-align: right;
                                display: block;
                                width: 100%;
                            }

                            .ansi1 {
                                font-size: medium !important;
                                font-weight: normal !important;
                            }

                            div[data-baseweb="select"] > div {
                                cursor: pointer !important;
                            }

                            [data-testid=StyledFullScreenButton] {
                                display: none;
                            }

                            [data-testid=stBottomBlockContainer] {
                                padding-bottom: 25px !important;
                            }

                        </style>
                   """